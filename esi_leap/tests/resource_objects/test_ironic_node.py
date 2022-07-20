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
from esi_leap.resource_objects import ironic_node
from esi_leap.tests import base
import mock

start = datetime.datetime(2016, 7, 16, 19, 20, 30)
fake_uuid = '13921c8d-ce11-4b6d-99ed-10e19d184e5f'


class FakeIronicNode(object):
    def __init__(self):
        self.created_at = start
        self.lessee = 'abcdef'
        self.owner = '123456'
        self.name = 'fake-node'
        self.properties = {'lease_uuid': '001'}
        self.provision_state = 'available'
        self.uuid = fake_uuid
        self.resource_class = 'baremetal'


class FakeLease(object):
    def __init__(self):
        self.uuid = '001'
        self.project_id = '654321'
        self.start_time = start + datetime.timedelta(days=5)
        self.end_time = start + datetime.timedelta(days=10)
        self.status = statuses.ACTIVE
        self.offer_uuid = '534653c9-880d-4c2d-6d6d-f4f2a09e384'


class TestIronicNode(base.TestCase):

    def setUp(self):
        super(TestIronicNode, self).setUp()
        self.fake_admin_project_id_1 = '123'
        self.fake_admin_project_id_2 = '123456'

    def test_resource_type(self):
        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        self.assertEqual('ironic_node', test_ironic_node.resource_type)

    def test_get_resource_uuid(self):
        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        self.assertEqual(fake_uuid, test_ironic_node.get_resource_uuid())

    @mock.patch('esi_leap.common.ironic.get_node_name')
    def test_get_resource_name(self, mock_gnn):
        mock_gnn.return_value = 'node-name'
        test_ironic_node = ironic_node.IronicNode(fake_uuid)

        resource_name = test_ironic_node.get_resource_name()

        self.assertEqual('node-name', resource_name)
        mock_gnn.assert_called_once_with(fake_uuid, None)

    @mock.patch.object(ironic_node, 'get_ironic_client', autospec=True)
    def test_get_by_name(self, client_mock):
        fake_get_node = FakeIronicNode()
        client_mock.return_value.node.get.return_value = fake_get_node
        test_ironic_node = ironic_node.IronicNode('node-name')
        self.assertEqual(fake_uuid, test_ironic_node.get_resource_uuid())
        client_mock.assert_called_once()
        client_mock.return_value.node.get.assert_called_once_with('node-name')

    @mock.patch.object(ironic_node, 'get_ironic_client', autospec=True)
    def test_get_lease_uuid(self, client_mock):
        fake_get_node = FakeIronicNode()
        client_mock.return_value.node.get.return_value = fake_get_node
        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        lease_uuid = test_ironic_node.get_lease_uuid()
        expected_lease_uuid = fake_get_node.properties.get('lease_uuid')
        self.assertEqual(lease_uuid, expected_lease_uuid)
        client_mock.assert_called_once()
        client_mock.return_value.node.get.assert_called_once_with(
            test_ironic_node._uuid)

    @mock.patch.object(ironic_node, 'get_ironic_client', autospec=True)
    def test_get_project_id(self, client_mock):
        fake_get_node = FakeIronicNode()
        client_mock.return_value.node.get.return_value = fake_get_node
        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        project_id = test_ironic_node.get_project_id()
        expected_project_id = fake_get_node.lessee
        self.assertEqual(project_id, expected_project_id)
        client_mock.assert_called_once()
        client_mock.return_value.node.get.assert_called_once_with(
            test_ironic_node._uuid)

    @mock.patch.object(ironic_node, 'get_ironic_client', autospec=True)
    def test_get_node_config(self, client_mock):
        fake_get_node = FakeIronicNode()
        client_mock.return_value.node.get.return_value = fake_get_node
        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        config = test_ironic_node.get_node_config()
        expected_config = fake_get_node.properties
        expected_config.pop('lease_uuid', None)
        self.assertEqual(config, expected_config)
        client_mock.assert_called_once()
        client_mock.return_value.node.get.assert_called_once_with(
            test_ironic_node._uuid)

    @mock.patch.object(ironic_node, 'get_ironic_client', autospec=True)
    def test_get_resource_class(self, client_mock):
        fake_get_node = FakeIronicNode()
        client_mock.return_value.node.get.return_value = fake_get_node
        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        resource_class = test_ironic_node.get_resource_class()
        expected_resource_class = fake_get_node.resource_class
        self.assertEqual(resource_class, expected_resource_class)
        client_mock.assert_called_once()
        client_mock.return_value.node.get.assert_called_once_with(
            test_ironic_node._uuid)

    @mock.patch.object(ironic_node, 'get_ironic_client', autospec=True)
    def test_set_lease(self, client_mock):
        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        fake_lease = FakeLease()
        test_ironic_node.set_lease(fake_lease)
        client_mock.assert_called_once()
        client_mock.return_value.node.update.assert_called_once()

    @mock.patch.object(ironic_node, 'get_ironic_client', autospec=True)
    def test_expire_lease(self, client_mock):
        client_mock.return_value.node.get.return_value.provision_state = (
            'active')

        with mock.patch.object(
            ironic_node.IronicNode, 'get_lease_uuid', autospec=True
        ) as mock_lease_uuid_true:
            fake_lease = FakeLease()
            mock_lease_uuid_true.return_value = fake_lease.uuid
            with mock.patch.object(
                ironic_node.IronicNode, 'get_project_id', autospec=True
            ) as mock_project_id_get:
                mock_project_id_get.return_value = fake_lease.project_id

                test_ironic_node = ironic_node.IronicNode(fake_uuid)
                test_ironic_node.expire_lease(fake_lease)

                mock_project_id_get.assert_called_once()
                mock_lease_uuid_true.assert_called_once()
                self.assertEqual(client_mock.call_count, 3)
                client_mock.return_value.node.update.assert_called_once()
                client_mock.return_value.node.get.assert_called_once_with(
                    test_ironic_node._uuid)
                client_mock.return_value.node.set_provision_state.\
                    assert_called_once_with(test_ironic_node._uuid, 'deleted')

        with mock.patch.object(
            ironic_node.IronicNode, 'get_lease_uuid', autospec=True
        ) as mock_lease_uuid_false:
            mock_lease_uuid_false.return_value = 'none'
            test_ironic_node = ironic_node.IronicNode(fake_uuid)
            fake_lease = FakeLease()
            test_ironic_node.expire_lease(fake_lease)
            mock_lease_uuid_false.assert_called_once()

    @mock.patch.object(ironic_node, 'get_ironic_client', autospec=True)
    def test_resource_admin_project_id(self, client_mock):
        fake_get_node = FakeIronicNode()
        client_mock.return_value.node.get.return_value = fake_get_node
        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        self.assertEqual(self.fake_admin_project_id_2,
                         test_ironic_node.resource_admin_project_id())
