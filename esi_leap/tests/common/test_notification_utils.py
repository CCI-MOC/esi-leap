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

import datetime

import mock

from esi_leap.common import notification_utils as notif_utils
from esi_leap.objects import fields
from esi_leap.objects import lease as lease_obj
from esi_leap.resource_objects.test_node import TestNode
from esi_leap.tests import base as tests_base


class NotifyTestCase(tests_base.TestCase):

    def setUp(self):
        super(NotifyTestCase, self).setUp()
        self.lease_notify_mock = mock.Mock()
        self.lease_notify_mock.__name__ = 'LeaseCRUDNotification'
        self.crud_notify_obj = {
            'lease': (self.lease_notify_mock,
                      lease_obj.LeaseCRUDPayload),
        }
        self.lease = lease_obj.Lease(
            id='12345',
            name='test_lease',
            start_time=datetime.datetime(2016, 7, 16, 19, 20, 30),
            end_time=datetime.datetime(2016, 8, 16, 19, 20, 30),
            fulfill_time=datetime.datetime(2016, 7, 16, 19, 21, 30),
            expire_time=datetime.datetime(2016, 8, 16, 19, 21, 30),
            uuid='13921c8d-ce11-4b6d-99ed-10e19d184e5f',
            resource_type='test_node',
            resource_uuid='111',
            project_id='lesseeid',
            owner_id='ownerid',
            parent_lease_uuid=None,
            offer_uuid=None,
            properties=None,
            status='created',
            purpose=None,
        )
        self.node = TestNode('test-node', '12345')

    def test_emit_notification(self):
        self.config(host='fake-host')
        test_level = fields.NotificationLevel.INFO
        test_status = fields.NotificationStatus.SUCCESS
        notif_utils._emit_notification(self.context,
                                       self.lease,
                                       'fulfill', test_level,
                                       test_status,
                                       self.crud_notify_obj,
                                       node=self.node)
        init_kwargs = self.lease_notify_mock.call_args[1]
        publisher = init_kwargs['publisher']
        event_type = init_kwargs['event_type']
        payload = init_kwargs['payload']
        level = init_kwargs['level']
        self.assertEqual('fake-host', publisher.host)
        self.assertEqual('esi-leap-manager', publisher.service)
        self.assertEqual('fulfill', event_type.action)
        self.assertEqual('lease', event_type.object)
        self.assertEqual(test_status, event_type.status)
        self.assertEqual(test_level, level)
        self.assertEqual(self.lease.name, payload.name)
        self.assertEqual(self.lease.uuid, payload.uuid)
        self.assertEqual(self.node.node_name, payload.node_name)
