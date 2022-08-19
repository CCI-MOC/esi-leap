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


class FakeIronicNode(object):
    def __init__(self):
        self.name = 'fake-node'
        self.owner = 'fake-project-uuid'
        self.uuid = 'fake-uuid'
        self.properties = {'lease_uuid': 'fake-lease-uuid'}
        self.lessee = 'fake-project-uuid'
        self.maintenance = False
        self.provision_state = 'active'


class FakeProject(object):
    def __init__(self):
        self.name = 'fake-project'
        self.id = 'fake-project-uuid'


class TestNodesController(test_api_base.APITestCase):

    def setUp(self):
        super(TestNodesController, self).setUp()

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.objects.offer.Offer.get_all')
    @mock.patch('esi_leap.objects.lease.Lease.get_all')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    def test_get_all(self, mock_gpl, mock_lga, mock_oga, mock_gnl):
        fake_node = FakeIronicNode()
        fake_project = FakeProject()
        mock_gnl.return_value = [fake_node]
        mock_oga.return_value = []
        mock_lga.return_value = []
        mock_gpl.return_value = [fake_project]

        data = self.get_json('/nodes')

        mock_gnl.assert_called_once_with(self.context)
        mock_oga.assert_called_once()
        mock_lga.assert_called_once()
        mock_gpl.assert_called_once()

        self.assertEqual(data['nodes'][0]['name'], 'fake-node')
        self.assertEqual(data['nodes'][0]['uuid'], 'fake-uuid')
        self.assertEqual(data['nodes'][0]['owner'], 'fake-project')
        self.assertEqual(data['nodes'][0]['lease_uuid'], 'fake-lease-uuid')
        self.assertEqual(data['nodes'][0]['lessee'], 'fake-project')
