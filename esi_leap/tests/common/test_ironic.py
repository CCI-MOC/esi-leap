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

from esi_leap.common import ironic
from esi_leap.tests import base


class FakeNode(object):
    def __init__(self):
        self.uuid = 'uuid'
        self.name = 'name'


class IronicTestCase(base.TestCase):

    @mock.patch.object(ironic, 'get_ironic_client', autospec=True)
    def test_get_node_name_no_list(self, mock_ironic):
        mock_ironic.return_value.node.get.return_value = FakeNode()

        node_name = ironic.get_node_name('12345')

        self.assertEqual('name', node_name)

    @mock.patch.object(ironic, 'get_ironic_client', autospec=True)
    def test_get_node_name_list(self, mock_ironic):
        node_list = [FakeNode()]
        node_name = ironic.get_node_name('uuid', node_list)

        self.assertEqual('name', node_name)

    @mock.patch.object(ironic, 'get_ironic_client', autospec=True)
    def test_get_node_name_list_no_match(self, mock_ironic):
        node_list = [FakeNode()]
        node_name = ironic.get_node_name('uuid2', node_list)

        self.assertEqual('', node_name)
