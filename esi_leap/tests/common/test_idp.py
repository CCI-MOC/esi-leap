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

from esi_leap.common import exception as e
from esi_leap.common import idp
from esi_leap.common.idp_clients import dummyIDP, keystoneIDP
from esi_leap.tests import base


class FakeProject(object):
    def __init__(self):
        self.id = "uuid"
        self.name = "name"


class IDPTestCase(base.TestCase):
    @mock.patch("oslo_utils.uuidutils.is_uuid_like")
    def test_get_project_uuid_from_ident_uuid(self, mock_iul):
        mock_iul.return_value = True

        project_uuid = idp.get_project_uuid_from_ident("uuid")

        mock_iul.assert_called_once_with("uuid")
        self.assertEqual("uuid", project_uuid)

    @mock.patch.object(idp, "get_idp_client", autospec=True)
    @mock.patch("oslo_utils.uuidutils.is_uuid_like")
    def test_get_project_uuid_from_ident_name(self, mock_iul, mock_keystone):
        mock_iul.return_value = False
        mock_keystone.return_value.list_projects.return_value = [FakeProject()]

        project_uuid = idp.get_project_uuid_from_ident("name")

        mock_iul.assert_called_once_with("name")
        self.assertEqual("uuid", project_uuid)
        mock_keystone.return_value.list_projects.assert_called_once_with(name="name")

    @mock.patch.object(idp, "get_idp_client", autospec=True)
    @mock.patch("oslo_utils.uuidutils.is_uuid_like")
    def test_get_project_uuid_from_ident_name_no_match(self, mock_iul, mock_keystone):
        mock_iul.return_value = False
        mock_keystone.return_value.list_projects.return_value = []

        self.assertRaises(e.ProjectNoSuchName, idp.get_project_uuid_from_ident, "name")

        mock_iul.assert_called_once_with("name")
        mock_keystone.return_value.list_projects.assert_called_once_with(name="name")

    @mock.patch.object(idp, "get_idp_client", autospec=True)
    def test_get_project_name_no_list(self, mock_keystone):
        mock_keystone.return_value.get_projects.return_value = FakeProject()

        project_name = idp.get_project_name("12345")

        self.assertEqual("name", project_name)

    @mock.patch.object(idp, "get_idp_client", autospec=True)
    def test_get_project_name_list(self, mock_keystone):
        project_list = [FakeProject()]
        project_name = idp.get_project_name("uuid", project_list)

        self.assertEqual("name", project_name)

    @mock.patch.object(idp, "get_idp_client", autospec=True)
    def test_get_project_name_list_no_match(self, mock_keystone):
        project_list = [FakeProject()]
        project_name = idp.get_project_name("uuid2", project_list)

        self.assertEqual("", project_name)

    @mock.patch.object(idp, "get_idp_client", autospec=True)
    def test_get_project_name_none(self, mock_keystone):
        project_list = [FakeProject()]
        project_name = idp.get_project_name(None, project_list)

        self.assertEqual("", project_name)


class KeystoneIDPTestCase(base.TestCase):
    @mock.patch("keystoneclient.client.Client")
    def test_get_projects(self, mock_kc):
        test_keystone_idp = keystoneIDP.KeystoneIDP()

        test_keystone_idp.get_projects(1)
        test_keystone_idp.cli.projects.get.assert_called_once_with(1)

    @mock.patch("keystoneclient.client.Client")
    def test_list_projects(self, mock_kc):
        test_keystone_idp = keystoneIDP.KeystoneIDP()

        test_keystone_idp.list_projects(foo="foo", bar=None)
        test_keystone_idp.cli.projects.list.assert_called_once_with(foo="foo", bar=None)


class DummyIDPTestCase(base.TestCase):
    def setUp(self):
        super().setUp()

        dummy_idp = dummyIDP.DummyIDP()
        dummy_idp.add_project(1, "P1", None)
        dummy_idp.add_project(2, "P2", None)
        dummy_idp.add_project(3, "P3", 1)

        self.dummy_idp = dummy_idp

    def test_get_projects(self):
        project = self.dummy_idp.get_projects(1)
        self.assertEqual([project.id, project.name, project.parent_id], [1, "P1", None])

        project = self.dummy_idp.get_projects(3)
        self.assertEqual([project.id, project.name, project.parent_id], [3, "P3", 1])

    def test_list_projects(self):
        project_list = self.dummy_idp.list_projects()
        self.assertEqual(len(project_list), 3)
        project_2 = project_list[1]

        self.assertEqual(
            [project_2.id, project_2.name, project_2.parent_id], [2, "P2", None]
        )
