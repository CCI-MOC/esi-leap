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

import esi_leap.conf
from esi_leap.resource_objects import base


CONF = esi_leap.conf.CONF
DUMMY_NODE_DIR = CONF.dummy_node.dummy_node_dir


class DummyNode(base.ResourceObjectInterface):

    resource_type = 'dummy_node'

    def __init__(self, uuid):
        self._uuid = uuid
        self._path = DUMMY_NODE_DIR + '/' + uuid

    def get_resource_uuid(self):
        return self._uuid

    def get_resource_name(self, resource_list=None):
        return 'dummy-node-%s' % self._uuid

    def get_lease_uuid(self):
        with open(self._path) as node_file:
            node_dict = json.load(node_file)
        return node_dict.get('lease_uuid', None)

    def get_project_id(self):
        with open(self._path) as node_file:
            node_dict = json.load(node_file)
        return node_dict.get('project_id', None)

    def get_node_config(self):
        with open(self._path) as node_file:
            node_dict = json.load(node_file)
        return node_dict.get('server_config', None)

    def get_resource_class(self):
        with open(self._path) as node_file:
            node_dict = json.load(node_file)
        return node_dict.get('resource_class', None)

    def set_lease(self, lease):
        with open(self._path) as node_file:
            node_dict = json.load(node_file)
        node_dict['lease_uuid'] = lease.uuid
        node_dict['project_id'] = lease.project_id
        with open(self._path, 'w') as node_file:
            json.dump(node_dict, node_file)

    def expire_lease(self, lease):
        with open(self._path) as node_file:
            node_dict = json.load(node_file)
        node_dict.pop('lease_uuid', None)
        node_dict.pop('project_id', None)
        with open(self._path, 'w') as node_file:
            json.dump(node_dict, node_file)

    def resource_admin_project_id(self):
        with open(self._path) as node_file:
            node_dict = json.load(node_file)
        return node_dict.get('project_owner_id', None)
