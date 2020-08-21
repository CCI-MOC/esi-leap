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
import datetime
from esi_leap.common import statuses
from esi_leap.resource_objects import test_node
from esi_leap.tests import base

start = datetime.datetime(2016, 7, 16, 19, 20, 30)


def get_test_contract():
    return {
        'id': 12345,
        'name': 'c',
        'uuid': '534653c9-880d-4c2d-6d6d-11111111111',
        'project_id': 'le55ee',
        'start_time': start + datetime.timedelta(days=5),
        'end_time': start + datetime.timedelta(days=10),
        'fulfill_time': start + datetime.timedelta(days=5),
        'expire_time': start + datetime.timedelta(days=10),
        'status': statuses.CREATED,
        'properties': {},
        'offer_uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'created_at': None,
        'updated_at': None
    }


class TestTestNode(base.TestCase):

    def setUp(self):
        super(TestTestNode, self).setUp()
        self.fake_test_node = test_node.TestNode('1111', '123456')
        self.fake_admin_project_id_1 = '123'
        self.fake_admin_project_id_2 = '123456'

    def test_get_contract_uuid(self):
        contract_uuid = self.fake_test_node.get_contract_uuid()
        self.assertEqual(contract_uuid, '12345')

    def test_get_project_id(self):
        project_id = self.fake_test_node.get_project_id()
        self.assertEqual(project_id, '123456')

    def test_get_node_config(self):
        config = self.fake_test_node.get_node_config()
        self.assertEqual(config, {})

    def test_set_contract(self):
        fake_contract = get_test_contract()
        self.assertEqual(
            self.fake_test_node.set_contract(
                fake_contract), None)

    def test_expire_contract(self):
        fake_contract = get_test_contract()
        self.assertEqual(
            self.fake_test_node.expire_contract(
                fake_contract), None)

    def test_is_resource_admin(self):
        res1 = self.fake_test_node.is_resource_admin(
            self.fake_admin_project_id_1)
        self.assertEqual(res1, False)
        res2 = self.fake_test_node.is_resource_admin(
            self.fake_admin_project_id_2)
        self.assertEqual(res2, True)
