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

from esi_leap.common import exception
from esi_leap.resource_objects.test_node import TestNode
from esi_leap.tests.api import base as test_api_base


class FakeEvent(object):
    def __init__(self):
        self.id = 1
        self.event_type = 'fake:event'
        self.event_time = datetime.now()
        self.object_type = 'lease'
        self.object_uuid = 'fake-lease-uuid'
        self.resource_type = 'fake_node'
        self.resource_uuid = 'fake-node-uuid'
        self.lessee_id = 'fake-lessee-id'
        self.owner_id = 'fake-owner-id'


class TestEventsController(test_api_base.APITestCase):

    def setUp(self):
        super(TestEventsController, self).setUp()

    @mock.patch('esi_leap.api.controllers.v1.utils.policy_authorize')
    @mock.patch('esi_leap.common.keystone.get_project_uuid_from_ident')
    @mock.patch('esi_leap.api.controllers.v1.event.get_resource_object')
    @mock.patch('esi_leap.objects.event.Event.get_all')
    def test_get_all(self, mock_ega, mock_gro, mock_gpufi, mock_pa):
        fake_event = FakeEvent()
        expected_filters = {}
        mock_pa.side_effect = None
        mock_ega.return_value = [fake_event]

        data = self.get_json('/events')

        mock_pa.assert_called_once()
        mock_gpufi.assert_not_called()
        mock_gro.assert_not_called()
        mock_ega.assert_called_once_with(expected_filters, self.context)

        self.assertEqual(data['events'][0]['id'], 1)

    @mock.patch('esi_leap.api.controllers.v1.utils.policy_authorize')
    @mock.patch('esi_leap.common.keystone.get_project_uuid_from_ident')
    @mock.patch('esi_leap.api.controllers.v1.event.get_resource_object')
    @mock.patch('esi_leap.objects.event.Event.get_all')
    def test_get_all_not_admin(self, mock_ega, mock_gro, mock_gpufi, mock_pa):
        fake_event = FakeEvent()
        expected_filters = {'lessee_or_owner_id': 'fake-lessee-id'}
        mock_pa.side_effect = exception.HTTPForbidden(
            rule='esi_leap:offer:offer_admin')
        mock_gpufi.return_value = 'fake-lessee-id'
        mock_ega.return_value = [fake_event]

        data = self.get_json('/events')

        mock_pa.assert_called_once()
        mock_gpufi.assert_called_once()
        mock_gro.assert_not_called()
        mock_ega.assert_called_once_with(expected_filters, self.context)

        self.assertEqual(data['events'][0]['id'], 1)

    @mock.patch('esi_leap.api.controllers.v1.utils.policy_authorize')
    @mock.patch('esi_leap.common.keystone.get_project_uuid_from_ident')
    @mock.patch('esi_leap.api.controllers.v1.event.get_resource_object')
    @mock.patch('esi_leap.objects.event.Event.get_all')
    def test_get_all_resource_filter(self, mock_ega, mock_gro, mock_gpufi,
                                     mock_pa):
        fake_event = FakeEvent()
        expected_filters = {'resource_type': 'test_node',
                            'resource_uuid': '1111'}
        mock_pa.side_effect = None
        mock_gro.return_value = TestNode('1111')
        mock_ega.return_value = [fake_event]

        data = self.get_json(
            '/events?resource_uuid=1111&resource_type=test_node')

        mock_pa.assert_called_once()
        mock_gpufi.assert_not_called()
        mock_gro.assert_called_with('test_node', '1111')
        mock_ega.assert_called_once_with(expected_filters, self.context)

        self.assertEqual(data['events'][0]['id'], 1)
