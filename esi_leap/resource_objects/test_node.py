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

    def __init__(self, uuid):
        self._uuid = uuid

    def get_contract_uuid(self):
        return '12345'

    def get_project_id(self):
        return '12345'

    def set_contract(self, contract):
        return

    def is_resource_admin(self, project_id):
        return True
