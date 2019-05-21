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

from esi_leap.common import ironic


class ResourceObject(object):

    def __init__(self, resource_type, resource_uuid):
        self._resource_type = resource_type
        self._resource_uuid = resource_uuid

    def get_project_id(self):
        return ironic.get_node_project_id(self._resource_uuid)

    def set_project_id(self, project_id):
        ironic.set_node_project_id(self._resource_uuid, project_id)

    def is_resource_admin(self, project_id):
        return (ironic.get_node_project_owner_id(self._resource_uuid)
                == project_id)
