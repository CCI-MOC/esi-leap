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

from ironicclient.common.apiclient import exceptions as ir_exception
import mock

from esi_leap.common import exception
from esi_leap.common import statuses
from esi_leap.resource_objects import ironic_node
from esi_leap.tests import base

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
        self.power_state = 'off'


class FakeLease(object):
    def __init__(self):
        self.uuid = '001'
        self.project_id = '654321'
        self.start_time = start + datetime.timedelta(days=5)
        self.end_time = start + datetime.timedelta(days=10)
        self.status = statuses.ACTIVE
        self.offer_uuid = '534653c9-880d-4c2d-6d6d-f4f2a09e384'


class TestIronicNode(base.TestCase):

    def test_resource_type(self):
        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        self.assertEqual('ironic_node', test_ironic_node.resource_type)

    def test_get_uuid(self):
        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        self.assertEqual(fake_uuid, test_ironic_node.get_uuid())

    @mock.patch('esi_leap.resource_objects.ironic_node.IronicNode._get_node')
    def test_get_name(self, mock_gn):
        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        fake_get_node = FakeIronicNode()
        mock_gn.return_value = fake_get_node

        self.assertEqual(fake_get_node.name, test_ironic_node.get_name())
        mock_gn.assert_called_once()

    @mock.patch.object(ironic_node, 'get_ironic_client', autospec=True)
    def test_init_with_name(self, mock_gn):
        fake_get_node = FakeIronicNode()
        mock_gn.return_value.node.get.return_value = fake_get_node
        test_ironic_node = ironic_node.IronicNode('node-name')

        self.assertEqual(fake_uuid, test_ironic_node.get_uuid())
        mock_gn.assert_called_once()
        mock_gn.return_value.node.get.assert_called_once_with('node-name')

    @mock.patch('esi_leap.resource_objects.ironic_node.IronicNode._get_node')
    def test_get_resource_class(self, mock_gn):
        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        fake_get_node = FakeIronicNode()
        mock_gn.return_value = fake_get_node

        resource_class = test_ironic_node.get_resource_class()
        self.assertEqual('baremetal', resource_class)
        mock_gn.assert_called_once()

    @mock.patch('esi_leap.resource_objects.ironic_node.IronicNode._get_node')
    def test_get_config(self, mock_gn):
        fake_get_node = FakeIronicNode()
        mock_gn.return_value = fake_get_node
        test_ironic_node = ironic_node.IronicNode(fake_uuid)

        config = test_ironic_node.get_config()
        expected_config = fake_get_node.properties
        self.assertEqual(config, expected_config)
        mock_gn.assert_called_once()

    @mock.patch('esi_leap.resource_objects.ironic_node.IronicNode._get_node')
    def test_get_owner_project_id(self, mock_gn):
        fake_get_node = FakeIronicNode()
        mock_gn.return_value = fake_get_node
        test_ironic_node = ironic_node.IronicNode(fake_uuid)

        self.assertEqual(test_ironic_node.get_owner_project_id(),
                         fake_get_node.owner)
        mock_gn.assert_called_once()

    @mock.patch('esi_leap.resource_objects.ironic_node.IronicNode._get_node')
    def test_get_lease_uuid(self, mock_gn):
        fake_get_node = FakeIronicNode()
        mock_gn.return_value = fake_get_node
        test_ironic_node = ironic_node.IronicNode(fake_uuid)

        self.assertEqual(test_ironic_node.get_lease_uuid(),
                         fake_get_node.properties.get('lease_uuid'))
        mock_gn.assert_called_once()

    @mock.patch('esi_leap.resource_objects.ironic_node.IronicNode._get_node')
    def test_get_lessee_project_id(self, mock_gn):
        fake_get_node = FakeIronicNode()
        mock_gn.return_value = fake_get_node
        test_ironic_node = ironic_node.IronicNode(fake_uuid)

        self.assertEqual(test_ironic_node.get_lessee_project_id(),
                         fake_get_node.lessee)
        mock_gn.assert_called_once()

    @mock.patch('esi_leap.resource_objects.ironic_node.IronicNode._get_node')
    def test_get_node_power_state(self, mock_gn):
        fake_get_node = FakeIronicNode()
        mock_gn.return_value = fake_get_node
        test_ironic_node = ironic_node.IronicNode(fake_uuid)

        self.assertEqual(test_ironic_node.get_node_power_state(),
                         fake_get_node.power_state)
        mock_gn.assert_called_once()

    @mock.patch('esi_leap.resource_objects.ironic_node.IronicNode._get_node')
    def test_get_node_provision_state(self, mock_gn):
        fake_get_node = FakeIronicNode()
        mock_gn.return_value = fake_get_node
        test_ironic_node = ironic_node.IronicNode(fake_uuid)

        self.assertEqual(test_ironic_node.get_node_provision_state(),
                         fake_get_node.provision_state)
        mock_gn.assert_called_once()

    @mock.patch.object(ironic_node, 'get_ironic_client', autospec=True)
    def test_set_lease(self, client_mock):
        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        fake_lease = FakeLease()

        test_ironic_node.set_lease(fake_lease)
        client_mock.assert_called_once()
        client_mock.return_value.node.update.assert_called_once_with(
            fake_uuid, [{'op': 'add',
                         'path': '/properties/lease_uuid',
                         'value': fake_lease.uuid},
                        {'op': 'add',
                         'path': '/lessee',
                         'value': fake_lease.project_id}])

    @mock.patch('esi_leap.resource_objects.ironic_node.IronicNode.'
                'get_lessee_project_id')
    @mock.patch('esi_leap.resource_objects.ironic_node.IronicNode.'
                'get_lease_uuid')
    @mock.patch('esi_leap.resource_objects.ironic_node.IronicNode._get_node')
    @mock.patch.object(ironic_node, 'get_ironic_client', autospec=True)
    def test_remove_lease(self, mock_client, mock_gn, mock_glu, mock_glpi):
        fake_get_node = FakeIronicNode()
        fake_get_node.provision_state = 'active'
        fake_lease = FakeLease()

        mock_gn.return_value = fake_get_node
        mock_glu.return_value = fake_lease.uuid
        mock_glpi.return_value = fake_lease.project_id

        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        test_ironic_node.remove_lease(fake_lease)

        mock_glpi.assert_called_once()
        mock_glu.assert_called_once()
        self.assertEqual(mock_gn.call_count, 1)
        self.assertEqual(mock_client.call_count, 2)
        mock_client.return_value.node.update.assert_called_once_with(
            fake_uuid, [{'op': 'remove', 'path': '/properties/lease_uuid'},
                        {'op': 'remove', 'path': '/lessee'}])
        mock_client.return_value.node.set_provision_state. \
            assert_called_once_with(fake_uuid, 'deleted')

    @mock.patch('esi_leap.resource_objects.ironic_node.IronicNode.'
                'get_lease_uuid')
    def test_expire_lease_no_match(self, mock_glu):
        mock_glu.return_value = 'none'
        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        fake_lease = FakeLease()

        test_ironic_node.remove_lease(fake_lease)
        mock_glu.assert_called_once()

    @mock.patch('esi_leap.common.ironic.get_node')
    def test_get_node(self, mock_gn):
        fake_get_node = FakeIronicNode()
        mock_gn.return_value = fake_get_node
        test_ironic_node = ironic_node.IronicNode(fake_uuid)

        self.assertEqual(test_ironic_node._get_node(), fake_get_node)
        mock_gn.assert_called_once_with(fake_uuid, None)

    @mock.patch('esi_leap.common.ironic.get_node')
    def test_get_node_cache(self, mock_gn):
        fake_get_node = FakeIronicNode()
        mock_gn.return_value = fake_get_node
        test_ironic_node = ironic_node.IronicNode(fake_uuid)
        test_ironic_node._node = fake_get_node

        self.assertEqual(fake_get_node,
                         test_ironic_node._get_node())
        mock_gn.assert_not_called()

    @mock.patch('esi_leap.common.ironic.get_node')
    def test_get_unknown_node(self, mock_gn):
        mock_gn.side_effect = ir_exception.NotFound
        test_unknown_node = ironic_node.IronicNode(fake_uuid)

        self.assertRaises(exception.NodeNotFound,
                          test_unknown_node._get_node)
