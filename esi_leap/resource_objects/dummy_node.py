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

import json
import os.path

from oslo_log import log as logging

from esi_leap.common import exception
import esi_leap.conf
from esi_leap.resource_objects import base


CONF = esi_leap.conf.CONF
DUMMY_NODE_DIR = CONF.dummy_node.dummy_node_dir

LOG = logging.getLogger(__name__)


class DummyNode(base.ResourceObjectInterface):

    resource_type = 'dummy_node'

    def __init__(self, uuid):
        self._uuid = uuid
        self._path = os.path.join(DUMMY_NODE_DIR, uuid)

    def get_resource_uuid(self):
        return self._uuid

    def get_resource_name(self, resource_list=None):
        return 'dummy-node-%s' % self._uuid

    def get_lease_uuid(self):
        return self._get_node_attr('lease_uuid', '',
                                   err_msg='Error getting lease UUID',
                                   err_val='unknown-lease-id')

    def get_project_id(self):
        return self._get_node_attr('project_id', '',
                                   err_msg='Error getting project ID',
                                   err_val='unknown-project-id')

    def get_node_config(self):
        return self._get_node_attr('server_config', {},
                                   err_msg='Error getting resource config')

    def get_resource_class(self, resource_list=None):
        return self._get_node_attr('resource_class', '',
                                   resource_list=resource_list,
                                   err_msg='Error getting resource class',
                                   err_val='unknown-class')

    def set_lease(self, lease):
        node_dict = self._get_node()
        node_dict['lease_uuid'] = lease.uuid
        node_dict['project_id'] = lease.project_id
        with open(self._path, 'w') as node_file:
            json.dump(node_dict, node_file)

    def expire_lease(self, lease):
        node_dict = self._get_node()
        node_dict.pop('lease_uuid', None)
        node_dict.pop('project_id', None)
        with open(self._path, 'w') as node_file:
            json.dump(node_dict, node_file)

    def resource_admin_project_id(self):
        return self._get_node_attr('project_owner_id', None,
                                   err_msg='Error getting resource admin '
                                           'project id',
                                   err_val='unknown-admin-id')

    def _get_node(self):
        try:
            with open(self._path) as node_file:
                return json.load(node_file)
        except FileNotFoundError as e:
            raise exception.NodeNotFound(uuid=self._uuid,
                                         resource_type=self.resource_type,
                                         err=str(e))

    def _get_node_attr(self, attr, default=None, resource_list=None,
                       err_val=None, err_msg=None):
        try:
            return self._get_node().get(attr, default)
        except exception.NodeNotFound:
            LOG.exception(err_msg)
            return err_val if err_val is not None else default
