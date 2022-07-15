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
from esi_leap.common import keystone
from esi_leap.tests import base


class FakeProject(object):
    def __init__(self):
        self.id = 'uuid'
        self.name = 'name'


class KeystoneTestCase(base.TestCase):

    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    def test_get_project_uuid_from_ident_uuid(self, mock_iul):
        mock_iul.return_value = True

        project_uuid = keystone.get_project_uuid_from_ident('uuid')

        mock_iul.assert_called_once_with('uuid')
        self.assertEqual('uuid', project_uuid)

    @mock.patch.object(keystone, 'get_keystone_client', autospec=True)
    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    def test_get_project_uuid_from_ident_name(self, mock_iul, mock_keystone):
        mock_iul.return_value = False
        mock_keystone.return_value.projects.list.return_value = [FakeProject()]

        project_uuid = keystone.get_project_uuid_from_ident('name')

        mock_iul.assert_called_once_with('name')
        self.assertEqual('uuid', project_uuid)
        mock_keystone.return_value.projects.list.assert_called_once_with(
            name='name')

    @mock.patch.object(keystone, 'get_keystone_client', autospec=True)
    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    def test_get_project_uuid_from_ident_name_no_match(self, mock_iul,
                                                       mock_keystone):
        mock_iul.return_value = False
        mock_keystone.return_value.projects.list.return_value = []

        self.assertRaises(e.ProjectNoSuchName,
                          keystone.get_project_uuid_from_ident,
                          'name')

        mock_iul.assert_called_once_with('name')
        mock_keystone.return_value.projects.list.assert_called_once_with(
            name='name')

    @mock.patch.object(keystone, 'get_keystone_client', autospec=True)
    def test_get_project_name_no_list(self, mock_keystone):
        mock_keystone.return_value.projects.get.return_value = FakeProject()

        project_name = keystone.get_project_name('12345')

        self.assertEqual('name', project_name)

    @mock.patch.object(keystone, 'get_keystone_client', autospec=True)
    def test_get_project_name_list(self, mock_keystone):
        project_list = [FakeProject()]
        project_name = keystone.get_project_name('uuid', project_list)

        self.assertEqual('name', project_name)

    @mock.patch.object(keystone, 'get_keystone_client', autospec=True)
    def test_get_project_name_list_no_match(self, mock_keystone):
        project_list = [FakeProject()]
        project_name = keystone.get_project_name('uuid2', project_list)

        self.assertEqual('', project_name)

    @mock.patch.object(keystone, 'get_keystone_client', autospec=True)
    def test_get_project_name_none(self, mock_keystone):
        project_list = [FakeProject()]
        project_name = keystone.get_project_name(None, project_list)

        self.assertEqual('', project_name)
