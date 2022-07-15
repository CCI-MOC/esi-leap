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
from esi_leap.resource_objects import dummy_node
from esi_leap.tests import base
import json
import mock


start = datetime.datetime(2016, 7, 16, 19, 20, 30)


def get_test_dummy_node_1():
    return {
        'project_owner_id': '123456',
        'project_id': '654321',
        'lease_uuid': '001',
        'resource_class': 'fake',
        'server_config': {
            'new attribute XYZ': 'new attribute XYZ',
            'cpu_type': 'Intel Xeon',
            'cores': 16,
            'ram_gb': 512,
            'storage_type': 'samsung SSD',
            'storage_size_gb': 204
        }
    }


def get_test_dummy_node_2():
    return {
        'project_owner_id': '123456',
        'resource_class': 'fake',
        'server_config': {
            'new attribute XYZ': 'new attribute XYZ',
            'cpu_type': 'Intel Xeon',
            'cores': 16,
            'ram_gb': 512,
            'storage_type': 'samsung SSD',
            'storage_size_gb': 204
        }
    }


class FakeLease(object):
    def __init__(self):
        self.uuid = '001'
        self.project_id = '654321'
        self.start_time = start + datetime.timedelta(days=5)
        self.end_time = start + datetime.timedelta(days=10)
        self.status = statuses.CREATED
        self.offer_uuid = '534653c9-880d-4c2d-6d6d-f4f2a09e384'


class TestDummyNode(base.TestCase):

    def setUp(self):
        super(TestDummyNode, self).setUp()
        self.fake_dummy_node = dummy_node.DummyNode('1111')
        self.fake_admin_project_id_1 = '123'
        self.fake_admin_project_id_2 = '123456'
        self.fake_read_data_1 = json.dumps(get_test_dummy_node_1())
        self.fake_read_data_2 = json.dumps(get_test_dummy_node_2())

    def test_resource_type(self):
        self.assertEqual('dummy_node', self.fake_dummy_node.resource_type)

    def test_get_resource_uuid(self):
        self.assertEqual('1111', self.fake_dummy_node.get_resource_uuid())

    def test_get_resource_name(self):
        self.assertEqual('dummy-node-1111',
                         self.fake_dummy_node.get_resource_name())

    def test_get_lease_uuid(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_1)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            lease_uuid = self.fake_dummy_node.get_lease_uuid()
            self.assertEqual(lease_uuid, '001')
            mock_file_open.assert_called_once()

    def test_get_project_id(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_1)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            project_id = self.fake_dummy_node.get_project_id()
            self.assertEqual(project_id, '654321')
            mock_file_open.assert_called_once()

    def test_get_node_config(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_1)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            config = self.fake_dummy_node.get_node_config()
            self.assertEqual(config, get_test_dummy_node_1()['server_config'])
            mock_file_open.assert_called_once()

    def test_get_resource_class(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_1)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            resource_class = self.fake_dummy_node.get_resource_class()
            self.assertEqual(resource_class,
                             get_test_dummy_node_1()['resource_class'])
            mock_file_open.assert_called_once()

    def test_set_lease(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_2)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            fake_lease = FakeLease()
            self.fake_dummy_node.set_lease(fake_lease)
            self.assertEqual(mock_file_open.call_count, 2)

    def test_expire_lease(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_1)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            fake_lease = FakeLease()
            self.fake_dummy_node.expire_lease(fake_lease)
            self.assertEqual(mock_file_open.call_count, 2)

    def test_resource_admin_project_id(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_1)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            self.assertEqual(self.fake_admin_project_id_2,
                             self.fake_dummy_node.resource_admin_project_id())
            self.assertEqual(mock_file_open.call_count, 1)
