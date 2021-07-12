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
from esi_leap.resource_objects import base


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


class IronicNode(base.ResourceObjectInterface):

    resource_type = 'ironic_node'

    def __init__(self, uuid):
        self._uuid = uuid

    @classmethod
    def get_by_name(cls, name):
        node = get_ironic_client().node.get(name)
        return IronicNode(node.uuid)

    def get_resource_uuid(self):
        return self._uuid

    def get_resource_name(self):
        node = get_ironic_client().node.get(self._uuid)
        return node.name

    def get_lease_uuid(self):
        node = get_ironic_client().node.get(self._uuid)
        return node.properties.get('lease_uuid', None)

    def get_project_id(self):
        node = get_ironic_client().node.get(self._uuid)
        return node.lessee

    def get_node_config(self):
        node = get_ironic_client().node.get(self._uuid)
        config = node.properties
        config.pop('lease_uuid', None)
        return config

    def set_lease(self, lease):
        patches = []
        patches.append({
            "op": "add",
            "path": "/properties/lease_uuid",
            "value": lease.uuid,
        })
        patches.append({
            "op": "add",
            "path": "/lessee",
            "value": lease.project_id,
        })
        get_ironic_client().node.update(self._uuid, patches)

    def expire_lease(self, lease):
        patches = []
        if self.get_lease_uuid() != lease.uuid:
            return
        if self.get_lease_uuid():
            patches.append({
                "op": "remove",
                "path": "/properties/lease_uuid",
            })
        if self.get_project_id():
            patches.append({
                "op": "remove",
                "path": "/lessee",
            })
        if len(patches) > 0:
            get_ironic_client().node.update(self._uuid, patches)
        state = get_ironic_client().node.get(self._uuid).provision_state
        if state == "active":
            get_ironic_client().node.set_provision_state(self._uuid, "deleted")

    def set_owner(self, owner_id):
        patches = [{
            "op": "add",
            "path": "/owner",
            "value": owner_id,
        }]
        get_ironic_client().node.update(self._uuid, patches)

    def resource_admin_project_id(self):
        node = get_ironic_client().node.get(self._uuid)
        return node.owner
