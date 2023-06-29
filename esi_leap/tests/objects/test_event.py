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

from esi_leap.objects import event as event_obj
from esi_leap.tests import base


class TestEventObject(base.DBTestCase):

    def setUp(self):
        super(TestEventObject, self).setUp()

        event_time = datetime.now()
        self.test_event_create_dict = {
            'event_type': 'fake:event',
            'event_time': event_time,
            'object_type': 'lease',
            'object_uuid': '11111',
            'resource_type': 'dummy_node',
            'resource_uuid': '22222',
            'lessee_id': '33333',
            'owner_id': '44444',
        }
        self.test_event_dict = {
            'id': 1,
            'event_type': 'fake:event',
            'event_time': event_time,
            'object_type': 'lease',
            'object_uuid': '11111',
            'resource_type': 'dummy_node',
            'resource_uuid': '22222',
            'lessee_id': '33333',
            'owner_id': '44444',
            'created_at': event_time,
            'updated_at': None,
        }

    @mock.patch('esi_leap.db.sqlalchemy.api.event_get_all')
    def test_get_all(self, mock_ega):
        event_obj.Event.get_all({}, self.context)
        mock_ega.assert_called_once_with({})

    @mock.patch('esi_leap.db.sqlalchemy.api.event_create')
    def test_create(self, mock_ec):
        mock_ec.return_value = self.test_event_dict
        event = event_obj.Event(self.context,
                                **self.test_event_create_dict)
        event.create()
        mock_ec.assert_called_once_with(self.test_event_create_dict)
