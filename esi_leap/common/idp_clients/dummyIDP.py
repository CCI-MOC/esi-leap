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

from keystoneclient.v3.projects import Project
from keystoneclient.v3.projects import ProjectManager
from keystoneclient.v3.users import User
from keystoneclient.v3.users import UserManager

from esi_leap.common.idp_clients import baseIDP


class DummyIDP(baseIDP.BaseIDP):
    dummy_project_dict = {}
    dummy_user_dict = {}

    def get_projects(self, project_id):
        return self.dummy_project_dict[project_id]

    def list_projects(self, **kwargs):
        return [project for project in self.dummy_project_dict.values()]

    def add_project(self, id, name, parent_id):
        self.dummy_project_dict[id] = Project(
            ProjectManager, {"id": id, "name": name, "parent_id": parent_id}
        )

    def add_user(self, id, name, project_id):
        self.dummy_user_dict[id] = User(
            UserManager, {"id": id, "name": name, "project_id": project_id}
        )
