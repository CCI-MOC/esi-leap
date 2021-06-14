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
from esi_leap.resource_objects import resource_object_factory as ro_factory
from esi_leap.tests import base


class TestResourceObjectFactory(base.TestCase):

    def setUp(self):
        super(TestResourceObjectFactory, self).setUp()

    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    def test_ironic_node(self, mock_iul):
        mock_iul.return_value = True
        node = ro_factory.ResourceObjectFactory.get_resource_object(
            'ironic_node', '1111')

        mock_iul.assert_called_once_with('1111')
        self.assertTrue(isinstance(node,
                                   resource_objects.ironic_node.IronicNode))
        self.assertEqual("1111", node.get_resource_uuid())

    @mock.patch('esi_leap.resource_objects.ironic_node.IronicNode.get_by_name')
    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    def test_ironic_node_by_name(self, mock_iul, mock_gbn):
        mock_iul.return_value = False
        mock_gbn.return_value = resource_objects.ironic_node.IronicNode('1111')
        node = ro_factory.ResourceObjectFactory.get_resource_object(
            'ironic_node', 'node-name')

        mock_iul.assert_called_once_with('node-name')
        mock_gbn.assert_called_once_with('node-name')
        self.assertTrue(isinstance(node,
                                   resource_objects.ironic_node.IronicNode))
        self.assertEqual("1111", node.get_resource_uuid())

    def test_dummy_node(self):
        node = ro_factory.ResourceObjectFactory.get_resource_object(
            'dummy_node', '1111')
        self.assertTrue(isinstance(node,
                                   resource_objects.dummy_node.DummyNode))
        self.assertEqual("1111", node.get_resource_uuid())

    def test_test_node(self):
        node = ro_factory.ResourceObjectFactory.get_resource_object(
            'test_node', '1111')
        self.assertTrue(isinstance(node,
                                   resource_objects.test_node.TestNode))
        self.assertEqual("1111", node.get_resource_uuid())

    def test_unknown_resource_type(self):
        self.assertRaises(exception.ResourceTypeUnknown,
                          ro_factory.ResourceObjectFactory.
                          get_resource_object,
                          'foo_node', '1111')
