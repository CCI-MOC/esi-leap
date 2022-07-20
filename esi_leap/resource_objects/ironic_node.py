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

from oslo_utils.uuidutils import is_uuid_like

from esi_leap.common import ironic
import esi_leap.conf
from esi_leap.resource_objects import base


CONF = esi_leap.conf.CONF
_cached_ironic_client = None


def get_ironic_client():
    global _cached_ironic_client
    if _cached_ironic_client is None:
        _cached_ironic_client = ironic.get_ironic_client()
    return _cached_ironic_client


class IronicNode(base.ResourceObjectInterface):

    resource_type = 'ironic_node'

    def __init__(self, ident):
        if not is_uuid_like(ident):
            node = get_ironic_client().node.get(ident)
            ident = node.uuid
        self._uuid = ident

    def get_resource_uuid(self):
        return self._uuid

    def get_resource_name(self, resource_list=None):
        return ironic.get_node_name(self._uuid, resource_list)

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

    def get_resource_class(self):
        node = get_ironic_client().node.get(self._uuid)
        return node.resource_class

    def set_lease(self, lease):
        patches = []
        patches.append({
            'op': 'add',
            'path': '/properties/lease_uuid',
            'value': lease.uuid,
        })
        patches.append({
            'op': 'add',
            'path': '/lessee',
            'value': lease.project_id,
        })
        get_ironic_client().node.update(self._uuid, patches)

    def expire_lease(self, lease):
        patches = []
        uuid = self.get_lease_uuid()
        if uuid != lease.uuid:
            return
        if uuid:
            patches.append({
                'op': 'remove',
                'path': '/properties/lease_uuid',
            })
        if self.get_project_id():
            patches.append({
                'op': 'remove',
                'path': '/lessee',
            })
        if len(patches) > 0:
            get_ironic_client().node.update(self._uuid, patches)
        state = get_ironic_client().node.get(self._uuid).provision_state
        if state == 'active':
            get_ironic_client().node.set_provision_state(self._uuid, 'deleted')

    def resource_admin_project_id(self):
        node = get_ironic_client().node.get(self._uuid)
        return node.owner
