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

from esi_leap.resource_objects import base


class TestNode(base.ResourceObjectInterface):

    resource_type = 'test_node'

    def __init__(self, uuid, project_id='12345'):
        self._uuid = uuid
        self._project_id = project_id

    def get_resource_uuid(self):
        return self._uuid

    def get_resource_name(self, resource_list=None):
        return 'test-node-%s' % self._uuid

    def get_lease_uuid(self):
        return '12345'

    def get_project_id(self):
        return self._project_id

    def get_node_config(self):
        return {}

    def get_resource_class(self):
        return 'fake'

    def set_lease(self, lease):
        return

    def expire_lease(self, lease):
        return

    def resource_admin_project_id(self):
        return self._project_id
