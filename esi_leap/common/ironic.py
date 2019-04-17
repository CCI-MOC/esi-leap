from keystoneauth1 import discover as ks_disc
from keystoneauth1 import loading as ks_loading

from ironicclient import client as ironic_client

from esi_leap.common import exception
import esi_leap.conf


CONF = esi_leap.conf.CONF
_cached_ironic_client = None

def get_ironic_client():
    global _cached_ironic_client
    if _cached_ironic_client is not None:
        return _cached_ironic_client
    
    auth_plugin = ks_loading.load_auth_from_conf_options(CONF, 'ironic')
    sess = ks_loading.load_session_from_conf_options(CONF, 'ironic',
                                                     auth=auth_plugin)

    try:
        ksa_adap = utils.get_ksa_adapter(
            'baremetal',
            ksa_auth=auth_plugin, ksa_session=sess)
        ironic_url = ksa_adap.get_endpoint()
    except:
        ironic_url = None

    kwargs = {}
    cli = ironic_client.get_client(1,
                                   endpoint=ironic_url,
                                   session=sess, **kwargs)
    _cached_ironic_client = cli

    return cli

def get_node_project_owner_id(node_uuid):
    node = get_ironic_client().node.get(node_uuid)
    return node.properties.get('project_owner_id', None)

def set_node_project_id(node_uuid, project_id):
    patch = {
        "op": "add",
        "path": "/properties/project_id",
        "value": project_id,
    }
    get_ironic_client().node.update(node_uuid, [patch])
