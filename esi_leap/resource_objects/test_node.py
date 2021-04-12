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


class TestNode(object):

    def __init__(self, uuid, project_id='12345'):
        self._uuid = uuid
        self._project_id = project_id

    def get_lease_uuid(self):
        return '12345'

    def get_project_id(self):
        return self._project_id

    def get_node_config(self):
        return {}

    def set_lease(self, lease):
        return

    def expire_lease(self, lease):
        return

    def is_resource_admin(self, project_id):
        return project_id == self._project_id
