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
        self.id = "uuid"
        self.name = "name"


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

    @mock.patch('esi_leap.common.keystone.get_project_list')
    def test_search_project_list(self, mock_gpl):
        test_project1 = mock.Mock(id='12345')
        test_project2 = mock.Mock(id='67890')
        test_project1.name = 'test-project-1'
        test_project2.name = 'test-project-2'

        mock_gpl.return_value = [test_project1, test_project2]

        project = keystone.search_project_list('67890')

        mock_gpl.assert_called_once()
        self.assertEqual(test_project2, project)

    @mock.patch('esi_leap.common.keystone.refresh_project_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    def test_search_project_list_refresh(self, mock_gpl, mock_rpl):
        test_project1 = mock.Mock(id='12345')
        test_project2 = mock.Mock(id='67890')
        test_project1.name = 'test-project-1'
        test_project2.name = 'test-project-2'

        mock_gpl.side_effect = [[test_project1],
                                [test_project1, test_project2]]

        project = keystone.search_project_list('67890')

        self.assertEqual(2, mock_gpl.call_count)
        mock_rpl.assert_called_once()
        self.assertEqual(test_project2, project)

    @mock.patch('esi_leap.common.keystone.search_project_list')
    def test_get_project_name(self, mock_spl):
        test_project = mock.Mock(id='12345', name='test-project')
        test_project.name = 'test-project'

        mock_spl.return_value = test_project

        project_name = keystone.get_project_name('12345')

        mock_spl.assert_called_once_with('12345')
        self.assertEqual('test-project', project_name)

    @mock.patch('esi_leap.common.keystone.search_project_list')
    def test_get_project_name_no_id(self, mock_spl):
        test_project = mock.Mock(id='12345', name='test-project')
        test_project.name = 'test-project'

        mock_spl.return_value = test_project

        project_name = keystone.get_project_name(None)

        mock_spl.assert_not_called()
        self.assertEqual('', project_name)

    @mock.patch('esi_leap.common.keystone.search_project_list')
    def test_get_project_name_no_match(self, mock_spl):
        mock_spl.return_value = None

        project_name = keystone.get_project_name('123456')

        mock_spl.assert_called_once_with('123456')
        self.assertEqual('', project_name)
