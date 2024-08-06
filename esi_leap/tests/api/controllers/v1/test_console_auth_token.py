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

import http.client as http_client
import mock
from oslo_utils import uuidutils

from esi_leap.common import ironic
from esi_leap.tests.api import base as test_api_base


class TestConsoleAuthTokensController(test_api_base.APITestCase):
    def setUp(self):
        super(TestConsoleAuthTokensController, self).setUp()
        self.node_uuid = uuidutils.generate_uuid()

    @mock.patch(
        "esi_leap.objects.console_auth_token.ConsoleAuthToken.authorize", autospec=True
    )
    @mock.patch.object(ironic, "get_ironic_client", autospec=True)
    def test_post(self, mock_client, mock_authorize):
        mock_authorize.return_value = "fake-token"

        data = {"node_uuid_or_name": self.node_uuid}

        request = self.post_json("/console_auth_tokens", data)

        mock_client.assert_called_once()
        mock_authorize.assert_called_once()
        self.assertEqual(http_client.CREATED, request.status_int)

    @mock.patch(
        "esi_leap.objects.console_auth_token.ConsoleAuthToken.authorize", autospec=True
    )
    @mock.patch.object(ironic, "get_ironic_client", autospec=True)
    def test_post_node_not_found(self, mock_client, mock_authorize):
        mock_client.return_value.node.get.return_value = None

        data = {"node_uuid_or_name": self.node_uuid}

        request = self.post_json("/console_auth_tokens", data, expect_errors=True)

        mock_client.assert_called_once()
        mock_authorize.assert_not_called()
        self.assertEqual(http_client.NOT_FOUND, request.status_int)

    @mock.patch(
        "esi_leap.objects.console_auth_token.ConsoleAuthToken.clean_console_tokens_for_node",
        autospec=True,
    )
    @mock.patch.object(ironic, "get_ironic_client", autospec=True)
    def test_delete(self, mock_client, mock_cctfn):
        request = self.delete_json("/console_auth_tokens/" + self.node_uuid)

        mock_client.assert_called_once()
        mock_cctfn.assert_called_once()
        self.assertEqual(http_client.OK, request.status_int)

    @mock.patch(
        "esi_leap.objects.console_auth_token.ConsoleAuthToken.clean_console_tokens_for_node",
        autospec=True,
    )
    @mock.patch.object(ironic, "get_ironic_client", autospec=True)
    def test_delete_node_not_found(self, mock_client, mock_cctfn):
        mock_client.return_value.node.get.return_value = None

        request = self.delete_json(
            "/console_auth_tokens/" + self.node_uuid, expect_errors=True
        )

        mock_client.assert_called_once()
        mock_cctfn.assert_not_called()
        self.assertEqual(http_client.NOT_FOUND, request.status_int)
