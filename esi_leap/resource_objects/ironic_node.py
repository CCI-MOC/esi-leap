#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from keystoneauth1 import loading as ks_loading

from ironicclient import client as ironic_client

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

    kwargs = {'os_ironic_api_version': '1.65'}
    cli = ironic_client.get_client(1,
                                   session=sess, **kwargs)
    _cached_ironic_client = cli

    return cli


class IronicNode(object):

    def __init__(self, uuid):
        self._uuid = uuid

    def get_contract_uuid(self):
        node = get_ironic_client().node.get(self._uuid)
        return node.properties.get('contract_uuid', None)

    def get_project_id(self):
        node = get_ironic_client().node.get(self._uuid)
        return node.lessee

    def get_node_config(self):
        node = get_ironic_client().node.get(self._uuid)
        config = node.properties
        config.pop('contract_uuid', None)
        return config

    def set_contract(self, contract):
        patches = []
        if contract is None:
            if self.get_contract_uuid():
                patches.append({
                    "op": "remove",
                    "path": "/properties/contract_uuid",
                })
            if self.get_project_id():
                patches.append({
                    "op": "remove",
                    "path": "/lessee",
                })
        else:
            patches.append({
                "op": "add",
                "path": "/properties/contract_uuid",
                "value": contract.uuid,
            })
            patches.append({
                "op": "add",
                "path": "/lessee",
                "value": contract.project_id,
            })
        if len(patches) > 0:
            get_ironic_client().node.update(self._uuid, patches)

    def is_resource_admin(self, project_id):
        node = get_ironic_client().node.get(self._uuid)
        project_owner_id = node.owner
        return (project_owner_id == project_id)
