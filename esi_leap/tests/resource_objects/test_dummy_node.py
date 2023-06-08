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
import json

import mock

from esi_leap.common import statuses
from esi_leap.resource_objects import dummy_node
from esi_leap.tests import base


start = datetime.datetime(2016, 7, 16, 19, 20, 30)


class FakeLease(object):
    def __init__(self):
        self.uuid = '001'
        self.project_id = '654321'
        self.start_time = start + datetime.timedelta(days=5)
        self.end_time = start + datetime.timedelta(days=10)
        self.status = statuses.CREATED
        self.offer_uuid = '534653c9-880d-4c2d-6d6d-f4f2a09e384'


class TestDummyNode(base.TestCase):

    test_node_1 = {
        'project_owner_id': '123456',
        'project_id': '654321',
        'lease_uuid': '001',
        'resource_class': 'fake',
        'power_state': 'off',
        'provision_state': 'enroll',
        'server_config': {
            'new attribute XYZ': 'new attribute XYZ',
            'cpu_type': 'Intel Xeon',
            'cores': 16,
            'ram_gb': 512,
            'storage_type': 'samsung SSD',
            'storage_size_gb': 204
        }
    }

    test_node_2 = {
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

    def setUp(self):
        super(TestDummyNode, self).setUp()
        self.fake_dummy_node = dummy_node.DummyNode('1111')
        self.fake_read_data_1 = json.dumps(self.test_node_1)
        self.fake_read_data_2 = json.dumps(self.test_node_2)

    def test_resource_type(self):
        self.assertEqual('dummy_node', self.fake_dummy_node.resource_type)

    def test_get_uuid(self):
        self.assertEqual('1111', self.fake_dummy_node.get_uuid())

    def test_get_name(self):
        self.assertEqual('dummy-node-1111',
                         self.fake_dummy_node.get_name())

    def test_get_resource_class(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_1)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            resource_class = self.fake_dummy_node.get_resource_class()
            self.assertEqual(resource_class,
                             self.test_node_1['resource_class'])
            mock_file_open.assert_called_once()

    def test_get_config(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_1)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            config = self.fake_dummy_node.get_config()
            self.assertEqual(config, self.test_node_1['server_config'])
            mock_file_open.assert_called_once()

    def test_get_owner_project_id(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_1)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            self.assertEqual(self.fake_dummy_node.get_owner_project_id(),
                             self.test_node_1['project_owner_id'])
            self.assertEqual(mock_file_open.call_count, 1)

    def test_get_lease_uuid(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_1)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            lease_uuid = self.fake_dummy_node.get_lease_uuid()
            self.assertEqual(lease_uuid, '001')
            mock_file_open.assert_called_once()

    def test_get_lessee_project_id(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_1)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            project_id = self.fake_dummy_node.get_lessee_project_id()
            self.assertEqual(project_id, '654321')
            mock_file_open.assert_called_once()

    def test_get_node_power_state(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_1)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            power_state = self.fake_dummy_node.get_node_power_state()
            self.assertEqual(power_state, 'off')
            mock_file_open.assert_called_once()

    def test_get_node_provision_state(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_1)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            provision_state = self.fake_dummy_node.get_node_provision_state()
            self.assertEqual(provision_state, 'enroll')
            mock_file_open.assert_called_once()

    def test_set_lease(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_2)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            fake_lease = FakeLease()
            self.fake_dummy_node.set_lease(fake_lease)
            self.assertEqual(mock_file_open.call_count, 2)

    def test_remove_lease(self):
        mock_open = mock.mock_open(read_data=self.fake_read_data_1)
        with mock.patch('builtins.open', mock_open) as mock_file_open:
            fake_lease = FakeLease()
            self.fake_dummy_node.remove_lease(fake_lease)
            self.assertEqual(mock_file_open.call_count, 2)

    @mock.patch('builtins.open')
    def test_get_deleted_node_info(self, mock_open):
        mock_open.side_effect = FileNotFoundError
        self.assertEqual(self.fake_dummy_node.get_resource_class(),
                         'unknown-class')
