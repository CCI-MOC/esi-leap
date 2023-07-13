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

from ironicclient.common.apiclient import exceptions as ir_exception
from oslo_log import log as logging
from oslo_utils.uuidutils import is_uuid_like

from esi_leap.common import exception
from esi_leap.common import ironic
import esi_leap.conf
from esi_leap.resource_objects import base
from esi_leap.resource_objects import error


CONF = esi_leap.conf.CONF
_cached_ironic_client = None

LOG = logging.getLogger(__name__)


def get_ironic_client():
    global _cached_ironic_client
    if _cached_ironic_client is None:
        _cached_ironic_client = ironic.get_ironic_client()
    return _cached_ironic_client


class IronicNode(base.ResourceObjectInterface):

    resource_type = 'ironic_node'

    def __init__(self, ident):
        if not is_uuid_like(ident):
            self._node = get_ironic_client().node.get(ident)
            self._uuid = self._node.uuid
        else:
            self._node = None
            self._uuid = ident

    def get_uuid(self):
        return self._uuid

    def get_name(self, resource_list=None):
        return self._get_node_attr('name', '',
                                   resource_list=resource_list,
                                   err_msg='Error getting resource name',
                                   err_val=error.UNKNOWN['name'])

    def get_resource_class(self, resource_list=None):
        return self._get_node_attr('resource_class', '',
                                   resource_list=resource_list,
                                   err_msg='Error getting resource class',
                                   err_val=error.UNKNOWN['resource_class'])

    def get_config(self):
        config = self._get_node_attr('properties', {},
                                     err_msg='Error getting resource config',
                                     err_val=error.UNKNOWN['config'])
        return config

    def get_owner_project_id(self):
        return self._get_node_attr('owner', '',
                                   err_msg='Error getting owner project id',
                                   err_val=error.UNKNOWN['owner_project_id'])

    def get_lease_uuid(self):
        props = self._get_node_attr('properties', None,
                                    err_msg='Error getting lease UUID',
                                    err_val=error.UNKNOWN['lease_uuid'])
        return None if props is None else props.get('lease_uuid', None)

    def get_lessee_project_id(self):
        return self._get_node_attr('lessee', '',
                                   err_msg='Error getting lessee project id',
                                   err_val=error.UNKNOWN['lessee_project_id'])

    def get_node_provision_state(self):
        return self._get_node_attr('provision_state', '',
                                   err_msg='Error getting provision state',
                                   err_val=error.UNKNOWN['provision_state'])

    def get_node_power_state(self):
        return self._get_node_attr('power_state', '',
                                   err_msg='Error getting power state',
                                   err_val=error.UNKNOWN['power_state'])

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

    def remove_lease(self, lease):
        patches = []
        uuid = self.get_lease_uuid()
        if uuid != lease.uuid:
            return
        if uuid:
            patches.append({
                'op': 'remove',
                'path': '/properties/lease_uuid',
            })
        if self.get_lessee_project_id():
            patches.append({
                'op': 'remove',
                'path': '/lessee',
            })
        if len(patches) > 0:
            get_ironic_client().node.update(self._uuid, patches)
        state = self._get_node().provision_state
        if state == 'active':
            get_ironic_client().node.set_provision_state(self._uuid, 'deleted')

    def _get_node(self, resource_list=None):
        try:
            if not self._node:
                self._node = ironic.get_node(self._uuid, resource_list)
        except ir_exception.NotFound as e:
            raise exception.NodeNotFound(uuid=self._uuid,
                                         resource_type=self.resource_type,
                                         err=str(e))
        return self._node

    def _get_node_attr(self, attr, default=None, resource_list=None,
                       err_val=None, err_msg=None):
        try:
            return getattr(self._get_node(resource_list), attr, default)
        except exception.NodeNotFound:
            LOG.exception(err_msg)
            return err_val if err_val is not None else default
