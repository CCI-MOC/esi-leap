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
import sys

from keystoneclient.v3.projects import Project
from keystoneclient.v3.projects import ProjectManager
from keystoneclient.v3.users import User
from keystoneclient.v3.users import UserManager
from oslo_utils import uuidutils

from esi_leap.common import exception
from esi_leap.common.idp import baseIDP


class DummyIDP(baseIDP.BaseIDP):
    dummy_project_dict = {}
    dummy_user_dict = {}

    def get_parent_project_id_tree(self, project_id):
        project = self._get_project_obj_from_id(project_id)
        project_ids = [project.id]
        while project.parent_id is not None:
            project = self._get_project_obj_from_id(project.parent_id)
            project_ids.append(project.id)
        return project_ids

    def get_project_uuid_from_ident(self, project_ident):
        if uuidutils.is_uuid_like(project_ident):
            return project_ident
        else:
            for p in self.dummy_project_dict.values():
                if p.name == project_ident:
                    return p.id
            raise exception.ProjectNoSuchName(name=project_ident)

    def get_project_list(self):
        return list(self.dummy_project_dict.values())

    def get_project_name(self, project_id, project_list=None):
        if project_id:
            if project_list is None:
                project = self._get_project_obj_from_id(project_id)
            else:
                project = next(
                    (p for p in project_list if getattr(p, "id") == project_id), None
                )
            return project.name if project else ""
        else:
            return ""

    def add_project(self, id, name, parent_id):
        self.dummy_project_dict[id] = Project(
            ProjectManager, {"id": id, "name": name, "parent_id": parent_id}
        )

    def add_user(self, id, name, project_id):
        self.dummy_user_dict[id] = User(
            UserManager, {"id": id, "name": name, "project_id": project_id}
        )

    def _get_project_obj_from_id(self, project_id):
        if p := self.dummy_project_dict.get(project_id, ""):
            return p
        sys.exit(f"No project with id {project_id} found")
