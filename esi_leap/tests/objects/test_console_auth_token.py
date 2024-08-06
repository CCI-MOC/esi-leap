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

from datetime import datetime
import mock

from oslo_db.exception import DBDuplicateEntry
from oslo_utils import uuidutils

from esi_leap.common import exception
from esi_leap.objects import console_auth_token
from esi_leap.tests import base


class TestConsoleAuthTokenObject(base.DBTestCase):
    def setUp(self):
        super(TestConsoleAuthTokenObject, self).setUp()

        self.token = uuidutils.generate_uuid()
        self.token_hash = console_auth_token.get_sha256_str(self.token)
        self.created_at = datetime.now()

        self.test_cat_dict = {
            "id": 1,
            "node_uuid": "test-node",
            "token": self.token,
            "expires": 1,
            "created_at": self.created_at,
            "updated_at": None,
        }

        self.test_authorized_cat_dict = {
            "id": 1,
            "node_uuid": "test-node",
            "token_hash": self.token_hash,
            "expires": 1,
            "created_at": self.created_at,
            "updated_at": None,
        }

        self.test_unauthorized_cat_dict = {
            "node_uuid": "test-node",
            "token": self.token,
            "expires": 1,
            "created_at": self.created_at,
            "updated_at": None,
        }

    def test_access_url_base(self):
        cat = console_auth_token.ConsoleAuthToken(self.context, **self.test_cat_dict)
        self.assertEqual("ws://0.0.0.0:6083", cat.access_url_base)

    def test_access_url(self):
        cat = console_auth_token.ConsoleAuthToken(self.context, **self.test_cat_dict)
        self.assertEqual("ws://0.0.0.0:6083/?token=%s" % self.token, cat.access_url)

    def test_access_url_unauthorized_token(self):
        cat = console_auth_token.ConsoleAuthToken(
            self.context, **self.test_unauthorized_cat_dict
        )
        self.assertEqual(None, cat.access_url)

    @mock.patch("esi_leap.db.sqlalchemy.api.console_auth_token_create")
    @mock.patch("oslo_utils.uuidutils.generate_uuid")
    def test_authorize(self, mock_gu, mock_catc):
        mock_gu.return_value = self.token
        mock_catc.return_value = self.test_authorized_cat_dict
        cat = console_auth_token.ConsoleAuthToken(
            self.context, **self.test_unauthorized_cat_dict
        )
        token = cat.authorize(10)
        mock_gu.assert_called_once()
        mock_catc.assert_called_once()
        self.assertEqual(self.token, token)

    def test_authorize_already_authorized(self):
        cat = console_auth_token.ConsoleAuthToken(self.context, **self.test_cat_dict)
        self.assertRaises(exception.TokenAlreadyAuthorized, cat.authorize, 10)

    @mock.patch("esi_leap.db.sqlalchemy.api.console_auth_token_create")
    @mock.patch("oslo_utils.uuidutils.generate_uuid")
    def test_authorize_duplicate_entry(self, mock_gu, mock_catc):
        mock_gu.return_value = self.token
        mock_catc.side_effect = DBDuplicateEntry()
        cat = console_auth_token.ConsoleAuthToken(
            self.context, **self.test_unauthorized_cat_dict
        )
        self.assertRaises(exception.TokenAlreadyAuthorized, cat.authorize, 10)
        mock_gu.assert_called_once()
        mock_catc.assert_called_once()

    @mock.patch("esi_leap.db.sqlalchemy.api.console_auth_token_get_by_token_hash")
    def test_validate(self, mock_catgbth):
        mock_catgbth.return_value = self.test_authorized_cat_dict
        console_auth_token.ConsoleAuthToken.validate(self.token)
        mock_catgbth.assert_called_once_with(self.token_hash)

    @mock.patch("esi_leap.db.sqlalchemy.api.console_auth_token_get_by_token_hash")
    def test_validate_invalid_token(self, mock_catgbth):
        mock_catgbth.return_value = None
        self.assertRaises(
            exception.InvalidToken,
            console_auth_token.ConsoleAuthToken.validate,
            self.token,
        )
        mock_catgbth.assert_called_once_with(self.token_hash)

    @mock.patch("esi_leap.db.sqlalchemy.api.console_auth_token_destroy_by_node_uuid")
    def test_clean_console_tokens_for_node(self, mock_catdbnu):
        console_auth_token.ConsoleAuthToken.clean_console_tokens_for_node("node-uuid")
        mock_catdbnu.assert_called_once_with("node-uuid")

    @mock.patch("esi_leap.db.sqlalchemy.api.console_auth_token_destroy_expired")
    def test_clean_expired_console_tokens(self, mock_catde):
        console_auth_token.ConsoleAuthToken.clean_expired_console_tokens()
        mock_catde.assert_called_once()
