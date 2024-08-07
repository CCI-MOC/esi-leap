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

import abc


class BaseIDP(abc.ABC):
    @abc.abstractmethod
    def get_project_list():
        pass

    @abc.abstractmethod
    def get_project_name(self, id, project_list=None):
        pass

    @abc.abstractmethod
    def get_parent_project_id_tree(project_id):
        pass

    @abc.abstractmethod
    def get_project_uuid_from_ident(project_ident):
        pass
