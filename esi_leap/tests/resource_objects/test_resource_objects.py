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

import mock

from esi_leap.common import exception
from esi_leap import resource_objects
from esi_leap.tests import base


class TestResourceObjects(base.TestCase):

    def test_get_type_valid(self):
        types = {'ironic_node': resource_objects.ironic_node.IronicNode,
                 'dummy_node': resource_objects.dummy_node.DummyNode,
                 'test_node': resource_objects.test_node.TestNode}

        for type_name, expected_type in types.items():
            self.assertEqual(resource_objects.get_type(type_name),
                             expected_type)

    def test_get_type_invalid(self):
        invalid_types = ('ahhhh', '', 1234, None, True)
        for type_name in invalid_types:
            self.assertRaises(exception.ResourceTypeUnknown,
                              resource_objects.get_type,
                              type_name)

    @mock.patch('esi_leap.resource_objects.get_type')
    def test_get_resource_object(self, mock_gt):
        mock_type = mock.MagicMock()
        mock_type.return_value = 'i have data!'
        mock_gt.return_value = mock_type
        obj = resource_objects.get_resource_object('fake_node', 'data')

        self.assertEqual(obj, 'i have data!')
        mock_type.assert_called_once_with('data')
        mock_gt.assert_called_once_with('fake_node')

    @mock.patch('esi_leap.resource_objects.ironic_node.is_uuid_like')
    def test_ironic_node(self, mock_iul):
        mock_iul.return_value = True
        node = resource_objects.get_resource_object('ironic_node', '1111')

        mock_iul.assert_called_once_with('1111')
        self.assertIsInstance(node, resource_objects.ironic_node.IronicNode)
        self.assertEqual('1111', node.get_uuid())

    @mock.patch('esi_leap.resource_objects.ironic_node.get_ironic_client')
    @mock.patch('esi_leap.resource_objects.ironic_node.is_uuid_like')
    def test_ironic_node_by_name(self, mock_iul, mock_gic):
        mock_ironic_client = mock.MagicMock()
        mock_ironic_node = mock.MagicMock()
        mock_uuid = mock.PropertyMock()
        mock_uuid.return_value = '1111'
        type(mock_ironic_node).uuid = mock_uuid
        mock_ironic_client.node.get.return_value = mock_ironic_node
        mock_gic.return_value = mock_ironic_client
        mock_iul.return_value = False
        node = resource_objects.get_resource_object('ironic_node', 'node-name')

        mock_iul.assert_called_with('node-name')
        mock_gic.assert_called_once_with()
        mock_uuid.assert_called_once_with()
        mock_ironic_client.node.get.assert_called_once_with('node-name')
        self.assertIsInstance(node, resource_objects.ironic_node.IronicNode)
        self.assertEqual('1111', node.get_uuid())

    def test_dummy_node(self):
        node = resource_objects.get_resource_object('dummy_node', '1111')

        self.assertIsInstance(node, resource_objects.dummy_node.DummyNode)
        self.assertEqual('1111', node.get_uuid())

    def test_test_node(self):
        node = resource_objects.get_resource_object('test_node', '1111')

        self.assertIsInstance(node, resource_objects.test_node.TestNode)
        self.assertEqual('1111', node.get_uuid())

    def test_unknown_resource_type(self):
        self.assertRaises(exception.ResourceTypeUnknown,
                          resource_objects.get_resource_object,
                          'foo_node', '1111')
