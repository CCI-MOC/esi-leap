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


CONF = esi_leap.conf.CONF
DUMMY_NODE_DIR = CONF.dummy_node.dummy_node_dir


class DummyNode(object):

    def __init__(self, uuid):
        self._uuid = uuid
        self._path = DUMMY_NODE_DIR + "/" + uuid

    def get_contract_uuid(self):
        with open(self._path) as node_file:
            node_dict = json.load(node_file)
        return node_dict.get("contract_uuid", None)

    def get_project_id(self):
        with open(self._path) as node_file:
            node_dict = json.load(node_file)
        return node_dict.get("project_id", None)

    def set_contract(self, contract):
        with open(self._path) as node_file:
            node_dict = json.load(node_file)
        if contract is None:
            node_dict.pop("contract_uuid", None)
            node_dict.pop("project_id", None)
        else:
            node_dict["contract_uuid"] = contract.uuid
            node_dict["project_id"] = contract.project_id
        with open(self._path, 'w') as node_file:
            json.dump(node_dict, node_file)

    def is_resource_admin(self, project_id):
        with open(self._path) as node_file:
            node_dict = json.load(node_file)
        project_owner_id = node_dict.get("project_owner_id", None)
        return (project_owner_id == project_id)
