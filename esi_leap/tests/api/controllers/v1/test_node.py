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

from esi_leap.tests.api import base as test_api_base
from esi_leap.common import ironic


class FakeIronicNode(object):
    def __init__(self):
        self.name = "fake-node"


class TestNodesController(test_api_base.APITestCase):

    def setUp(self):
        super(TestNodesController, self).setUp()

    @mock.patch.object(ironic, 'get_ironic_client', autospec=True)
    def test_get_all(self, client_mock):
        fake_node = FakeIronicNode()
        client_mock.return_value.node.list.return_value = [fake_node]
        data = self.get_json("/nodes")
        client_mock.assert_called_once()
        self.assertEqual(data["nodes"][0]["name"], "fake-node")
