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
from oslo_utils import uuidutils
import tempfile
import threading

from esi_leap.common import exception
from esi_leap.common import statuses
from esi_leap.objects import fields as obj_fields
from esi_leap.objects import lease as lease_obj
from esi_leap.objects import offer as offer_obj
from esi_leap.resource_objects.test_node import TestNode
from esi_leap.tests import base


class TestLeaseObject(base.DBTestCase):

    def setUp(self):
        super(TestLeaseObject, self).setUp()

        self.start_time = datetime.datetime(2016, 7, 16, 19, 20, 30)
        self.test_offer = offer_obj.Offer(
            id=27,
            uuid=uuidutils.generate_uuid(),
            project_id='01d4e6a72f5c408813e02f664cc8c83e',
            resource_type='dummy_node',
            resource_uuid='1718',
            start_time=self.start_time,
            end_time=self.start_time + datetime.timedelta(days=100),
            status=statuses.AVAILABLE,
            properties={'floor_price': 3},
        )
        self.test_parent_lease = lease_obj.Lease(
            uuid=uuidutils.generate_uuid(),
            status=statuses.ACTIVE,
        )
        self.test_parent_lease_expired = lease_obj.Lease(
            uuid=uuidutils.generate_uuid(),
            status=statuses.EXPIRED,
        )
        self.test_lease_dict = {
            'id': 28,
            'name': 'lease',
            'uuid': uuidutils.generate_uuid(),
            'project_id': 'le55ee',
            'owner_id': '0wn3r',
            'start_time': self.start_time + datetime.timedelta(days=5),
            'end_time': self.start_time + datetime.timedelta(days=10),
            'fulfill_time': self.start_time + datetime.timedelta(days=5),
            'expire_time': self.start_time + datetime.timedelta(days=10),
            'status': statuses.CREATED,
            'properties': {},
            'resource_type': 'dummy_node',
            'resource_uuid': '1718',
            'purpose': 'test_purpose',
            'offer_uuid': None,
            'parent_lease_uuid': None,
            'created_at': None,
            'updated_at': None
        }
        self.test_lease_offer_dict = self.test_lease_dict.copy()
        self.test_lease_offer_dict['offer_uuid'] = self.test_offer.uuid
        self.test_lease_parent_lease_dict = self.test_lease_dict.copy()
        self.test_lease_parent_lease_dict['parent_lease_uuid'] = (
            'parent-lease-uuid')
        self.test_lease_create_dict = {
            'name': 'lease_create',
            'project_id': 'le55ee',
            'owner_id': '0wn3r',
            'start_time': self.start_time + datetime.timedelta(days=5),
            'end_time': self.start_time + datetime.timedelta(days=10),
            'resource_type': 'dummy_node',
            'resource_uuid': '1718',
            'purpose': 'test_purpose',
        }
        self.test_lease_create_offer_dict = self.test_lease_create_dict.copy()
        self.test_lease_create_offer_dict['offer_uuid'] = self.test_offer.uuid
        self.test_lease_create_parent_lease_dict = (
            self.test_lease_create_dict.copy())
        self.test_lease_create_parent_lease_dict['parent_lease_uuid'] = (
            'parent-lease-uuid')

        self.config(lock_path=tempfile.mkdtemp(), group='oslo_concurrency')

    def test_get(self):
        lease_uuid = self.test_lease_dict['uuid']
        with mock.patch.object(self.db_api, 'lease_get_by_uuid',
                               autospec=True) as mock_lease_get_by_uuid:
            mock_lease_get_by_uuid.return_value = self.test_lease_dict

            lease = lease_obj.Lease.get(lease_uuid, self.context)

            mock_lease_get_by_uuid.assert_called_once_with(lease_uuid)
            self.assertEqual(self.context, lease._context)

    def test_get_all(self):
        with mock.patch.object(
                self.db_api, 'lease_get_all', autospec=True
        ) as mock_lease_get_all:
            mock_lease_get_all.return_value = [self.test_lease_dict,
                                               self.test_lease_offer_dict]

            leases = lease_obj.Lease.get_all({}, self.context)

            mock_lease_get_all.assert_called_once_with({})
            self.assertEqual(len(leases), 2)
            self.assertIsInstance(leases[0], lease_obj.Lease)
            self.assertEqual(self.context, leases[0]._context)

    @mock.patch('esi_leap.db.sqlalchemy.api.resource_verify_availability')
    @mock.patch('esi_leap.db.sqlalchemy.api.offer_verify_availability')
    @mock.patch('esi_leap.objects.offer.Offer.get')
    @mock.patch('esi_leap.db.sqlalchemy.api.lease_create')
    def test_create(self, mock_lc, mock_og, mock_ova, mock_rva):
        lease = lease_obj.Lease(self.context, **self.test_lease_create_dict)
        mock_lc.return_value = self.test_lease_dict

        lease.create()

        mock_lc.assert_called_once_with(self.test_lease_create_dict)
        mock_og.assert_not_called
        mock_ova.assert_not_called
        mock_rva.assert_called_once_with(lease.resource_type,
                                         lease.resource_uuid,
                                         lease.start_time,
                                         lease.end_time)

    @mock.patch('esi_leap.db.sqlalchemy.api.resource_verify_availability')
    @mock.patch('esi_leap.db.sqlalchemy.api.offer_verify_availability')
    @mock.patch('esi_leap.objects.offer.Offer.get')
    @mock.patch('esi_leap.db.sqlalchemy.api.lease_create')
    def test_create_with_offer(self, mock_lc, mock_og, mock_ova, mock_rva):
        lease = lease_obj.Lease(self.context,
                                **self.test_lease_create_offer_dict)
        mock_lc.return_value = self.test_lease_offer_dict
        mock_og.return_value = self.test_offer

        lease.create()

        mock_lc.assert_called_once_with(self.test_lease_create_offer_dict)
        mock_og.assert_called_once_with(lease.offer_uuid)
        mock_ova.assert_called_once_with(self.test_offer,
                                         lease.start_time,
                                         lease.end_time)
        mock_rva.assert_not_called

    @mock.patch('esi_leap.db.sqlalchemy.api.lease_verify_child_availability')
    @mock.patch('esi_leap.objects.lease.Lease.get')
    @mock.patch('esi_leap.db.sqlalchemy.api.lease_create')
    def test_create_with_parent_lease(self, mock_lc, mock_lg, mock_lvca):
        lease = lease_obj.Lease(self.context,
                                **self.test_lease_create_parent_lease_dict)
        mock_lc.return_value = self.test_lease_offer_dict
        mock_lg.return_value = self.test_parent_lease

        lease.create()

        mock_lc.assert_called_once_with(
            self.test_lease_create_parent_lease_dict)
        mock_lg.assert_called_once_with('parent-lease-uuid')
        mock_lvca.assert_called_once_with(self.test_parent_lease,
                                          lease.start_time,
                                          lease.end_time)

    @mock.patch('esi_leap.db.sqlalchemy.api.lease_verify_child_availability')
    @mock.patch('esi_leap.objects.lease.Lease.get')
    @mock.patch('esi_leap.db.sqlalchemy.api.lease_create')
    def test_create_with_parent_lease_expired(self, mock_lc, mock_lg,
                                              mock_lvca):
        lease = lease_obj.Lease(self.context,
                                **self.test_lease_create_parent_lease_dict)
        mock_lg.return_value = self.test_parent_lease_expired

        self.assertRaises(exception.LeaseNotActive, lease.create)

        mock_lc.assert_not_called()
        mock_lg.assert_called_once_with('parent-lease-uuid')
        mock_lvca.assert_not_called()

    def test_create_invalid_time(self):
        bad_lease = {
            'id': 30,
            'name': 'bad-lease',
            'uuid': '534653c9-880d-4c2d-6d6d-44444444444',
            'project_id': 'le55ee_2',
            'owner_id': 'ownerid',
            'resource_type': 'dummy_node',
            'resource_uuid': '1111',
            'start_time': self.start_time + datetime.timedelta(days=30),
            'end_time': self.start_time + datetime.timedelta(days=20),
            'fulfill_time': self.start_time + datetime.timedelta(days=35),
            'expire_time': self.start_time + datetime.timedelta(days=40),
        }

        lease = lease_obj.Lease(self.context, **bad_lease)

        self.assertRaises(exception.InvalidTimeRange, lease.create)

    def test_create_concurrent_offer_conflict(self):
        lease = lease_obj.Lease(self.context,
                                **self.test_lease_create_offer_dict)

        lease2 = lease_obj.Lease(self.context,
                                 **self.test_lease_create_offer_dict)

        lease2.id = 28

        with mock.patch.object(self.db_api, 'lease_create',
                               autospec=True) as mock_lease_create:
            with mock.patch.object(offer_obj.Offer, 'get',
                                   autospec=True) as mock_offer_get:
                with mock.patch.object(self.db_api,
                                       'offer_verify_availability',
                                       autospec=True) as mock_ovca:

                    mock_offer_get.return_value = self.test_offer

                    def update_mock(updates):
                        mock_ovca.side_effect = Exception('bad')

                    mock_lease_create.side_effect = update_mock

                    thread = threading.Thread(target=lease.create)
                    thread2 = threading.Thread(target=lease2.create)

                    thread.start()
                    thread2.start()

                    thread.join()
                    thread2.join()

                    assert mock_offer_get.call_count == 2
                    assert mock_ovca.call_count == 2
                    mock_lease_create.assert_called_once()

    @mock.patch('esi_leap.objects.lease.Lease.resource_object')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.set_lease')
    @mock.patch('esi_leap.objects.lease.Lease.save')
    @mock.patch('esi_leap.common.notification_utils'
                '._emit_notification')
    def test_fulfill(self, mock_notify,
                     mock_save, mock_set_lease, mock_ro):
        lease = lease_obj.Lease(self.context, **self.test_lease_dict)
        test_node = TestNode('test-node', '12345')

        mock_ro.return_value = test_node

        lease.fulfill()

        mock_notify.assert_has_calls([mock.call(mock.ANY, mock.ANY, 'fulfill',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.START,
                                      mock.ANY, node=mock.ANY),
                                      mock.call(mock.ANY, mock.ANY, 'fulfill',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.END,
                                      mock.ANY, node=mock.ANY)])
        mock_ro.assert_called_once()
        mock_set_lease.assert_called_once()
        mock_save.assert_called_once()
        self.assertEqual(lease.status, statuses.ACTIVE)

    @mock.patch('esi_leap.objects.lease.Lease.resource_object')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.set_lease')
    @mock.patch('esi_leap.objects.lease.Lease.save')
    @mock.patch('esi_leap.common.notification_utils'
                '._emit_notification')
    def test_fulfill_error(self, mock_notify, mock_save,
                           mock_set_lease, mock_ro):
        lease = lease_obj.Lease(self.context, **self.test_lease_dict)
        test_node = TestNode('test-node', '12345')

        mock_ro.return_value = test_node
        mock_set_lease.side_effect = Exception('bad')

        lease.fulfill()

        mock_notify.assert_has_calls([mock.call(mock.ANY, mock.ANY, 'fulfill',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.START,
                                      mock.ANY, node=mock.ANY),
                                      mock.call(mock.ANY, mock.ANY, 'fulfill',
                                      obj_fields.NotificationLevel.ERROR,
                                      obj_fields.NotificationStatus.ERROR,
                                      mock.ANY, node=mock.ANY)])
        mock_ro.assert_called_once()
        mock_set_lease.assert_called_once()
        mock_save.assert_called_once()
        self.assertEqual(lease.status, statuses.WAIT_FULFILL)

    @mock.patch('esi_leap.resource_objects.test_node.TestNode.set_lease')
    @mock.patch('esi_leap.objects.lease.Lease.get')
    @mock.patch('esi_leap.objects.lease.Lease.resource_object')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.get_lease_uuid')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.remove_lease')
    @mock.patch('esi_leap.objects.lease.Lease.save')
    @mock.patch('esi_leap.common.notification_utils'
                '._emit_notification')
    def test_cancel(self, mock_notify, mock_save,
                    mock_rl, mock_glu, mock_ro,
                    mock_lg, mock_sl):
        lease = lease_obj.Lease(self.context, **self.test_lease_dict)
        test_node = TestNode('test-node', '12345')

        mock_ro.return_value = test_node
        mock_glu.return_value = lease.uuid

        lease.cancel()
        mock_notify.assert_has_calls([mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.START,
                                      mock.ANY, node=mock.ANY),
                                      mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.END,
                                      mock.ANY, node=mock.ANY)])
        mock_sl.assert_not_called()
        mock_lg.assert_not_called()
        mock_ro.assert_called_once()
        mock_glu.assert_called_once()
        mock_rl.assert_called_once()
        mock_save.assert_called_once()
        self.assertEqual(lease.status, statuses.DELETED)

    @mock.patch('esi_leap.resource_objects.test_node.TestNode.set_lease')
    @mock.patch('esi_leap.objects.lease.Lease.get')
    @mock.patch('esi_leap.objects.lease.Lease.resource_object')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.get_lease_uuid')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.remove_lease')
    @mock.patch('esi_leap.objects.lease.Lease.save')
    @mock.patch('esi_leap.common.notification_utils'
                '._emit_notification')
    def test_cancel_error(self, mock_notify, mock_save,
                          mock_rl, mock_glu,
                          mock_ro, mock_lg, mock_sl):
        lease = lease_obj.Lease(self.context, **self.test_lease_dict)
        test_node = TestNode('test-node', '12345')

        mock_ro.return_value = test_node
        mock_glu.return_value = lease.uuid
        mock_rl.side_effect = Exception('bad')

        lease.cancel()

        mock_notify.assert_has_calls([mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.START,
                                      mock.ANY, node=mock.ANY),
                                      mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.ERROR,
                                      obj_fields.NotificationStatus.ERROR,
                                      mock.ANY, node=mock.ANY)])
        mock_sl.assert_not_called()
        mock_lg.assert_not_called()
        mock_ro.assert_called_once()
        mock_glu.assert_called_once()
        mock_rl.assert_called_once()
        mock_save.assert_called_once()
        self.assertEqual(lease.status, statuses.WAIT_CANCEL)

    @mock.patch('esi_leap.resource_objects.test_node.TestNode.set_lease')
    @mock.patch('esi_leap.objects.lease.Lease.get')
    @mock.patch('esi_leap.objects.lease.Lease.resource_object')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.get_lease_uuid')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.remove_lease')
    @mock.patch('esi_leap.objects.lease.Lease.save')
    @mock.patch('esi_leap.common.notification_utils'
                '._emit_notification')
    def test_cancel_with_parent(self, mock_notify, mock_save,
                                mock_rl, mock_glu,
                                mock_ro, mock_lg, mock_sl):
        lease = lease_obj.Lease(self.context,
                                **self.test_lease_parent_lease_dict)
        test_node = TestNode('test-node', '12345')

        mock_ro.return_value = test_node
        mock_glu.return_value = lease.uuid

        lease.cancel()

        mock_notify.assert_has_calls([mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.START,
                                      mock.ANY, node=mock.ANY),
                                      mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.END,
                                      mock.ANY, node=mock.ANY)])
        mock_sl.assert_called_once()
        mock_lg.assert_called_once()
        mock_ro.assert_called_once()
        mock_glu.assert_called_once()
        mock_rl.assert_called_once()
        mock_save.assert_called_once()
        self.assertEqual(lease.status, statuses.DELETED)

    @mock.patch('esi_leap.objects.lease.Lease.resource_object')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.get_lease_uuid')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.remove_lease')
    @mock.patch('esi_leap.objects.lease.Lease.save')
    @mock.patch('esi_leap.common.notification_utils'
                '._emit_notification')
    def test_cancel_no_expire(self, mock_notify, mock_save,
                              mock_rl, mock_glu,
                              mock_ro):
        lease = lease_obj.Lease(self.context, **self.test_lease_dict)
        test_node = TestNode('test-node', '12345')

        mock_ro.return_value = test_node
        mock_glu.return_value = 'some-other-lease-uuid'

        lease.cancel()

        mock_notify.assert_has_calls([mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.START,
                                      mock.ANY, node=mock.ANY),
                                      mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.END,
                                      mock.ANY, node=mock.ANY)])
        mock_ro.assert_called_once()
        mock_glu.assert_called_once()
        mock_rl.assert_not_called()
        mock_save.assert_called_once()
        self.assertEqual(lease.status, statuses.DELETED)

    @mock.patch('esi_leap.resource_objects.test_node.TestNode.set_lease')
    @mock.patch('esi_leap.objects.lease.Lease.get')
    @mock.patch('esi_leap.objects.lease.Lease.resource_object')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.get_lease_uuid')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.remove_lease')
    @mock.patch('esi_leap.objects.lease.Lease.save')
    @mock.patch('esi_leap.common.notification_utils'
                '._emit_notification')
    def test_expire(self, mock_notify, mock_save, mock_rl, mock_glu, mock_ro,
                    mock_lg, mock_sl):
        lease = lease_obj.Lease(self.context, **self.test_lease_dict)
        test_node = TestNode('test-node', '12345')

        mock_ro.return_value = test_node
        mock_glu.return_value = lease.uuid

        lease.expire()

        mock_notify.assert_has_calls([mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.START,
                                      mock.ANY, node=mock.ANY),
                                      mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.END,
                                      mock.ANY, node=mock.ANY)])
        mock_sl.assert_not_called()
        mock_lg.assert_not_called()
        mock_ro.assert_called_once()
        mock_glu.assert_called_once()
        mock_rl.assert_called_once()
        mock_save.assert_called_once()
        self.assertEqual(lease.status, statuses.EXPIRED)

    @mock.patch('esi_leap.resource_objects.test_node.TestNode.set_lease')
    @mock.patch('esi_leap.objects.lease.Lease.get')
    @mock.patch('esi_leap.objects.lease.Lease.resource_object')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.get_lease_uuid')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.remove_lease')
    @mock.patch('esi_leap.objects.lease.Lease.save')
    @mock.patch('esi_leap.common.notification_utils'
                '._emit_notification')
    def test_expire_error(self, mock_notify, mock_save, mock_rl, mock_glu,
                          mock_ro, mock_lg, mock_sl):
        lease = lease_obj.Lease(self.context, **self.test_lease_dict)
        test_node = TestNode('test-node', '12345')

        mock_ro.return_value = test_node
        mock_glu.return_value = lease.uuid
        mock_rl.side_effect = Exception('bad')

        lease.expire()

        mock_notify.assert_has_calls([mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.START,
                                      mock.ANY, node=mock.ANY),
                                      mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.ERROR,
                                      obj_fields.NotificationStatus.ERROR,
                                      mock.ANY, node=mock.ANY)])
        mock_sl.assert_not_called()
        mock_lg.assert_not_called()
        mock_ro.assert_called_once()
        mock_glu.assert_called_once()
        mock_rl.assert_called_once()
        mock_save.assert_called_once()
        self.assertEqual(lease.status, statuses.WAIT_EXPIRE)

    @mock.patch('esi_leap.resource_objects.test_node.TestNode.set_lease')
    @mock.patch('esi_leap.objects.lease.Lease.get')
    @mock.patch('esi_leap.objects.lease.Lease.resource_object')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.get_lease_uuid')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.remove_lease')
    @mock.patch('esi_leap.objects.lease.Lease.save')
    @mock.patch('esi_leap.common.notification_utils'
                '._emit_notification')
    def test_expire_with_parent(self, mock_notify, mock_save, mock_rl,
                                mock_glu, mock_ro, mock_lg, mock_sl):
        lease = lease_obj.Lease(self.context,
                                **self.test_lease_parent_lease_dict)
        test_node = TestNode('test-node', '12345')

        mock_ro.return_value = test_node
        mock_glu.return_value = lease.uuid

        lease.expire()

        mock_notify.assert_has_calls([mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.START,
                                      mock.ANY, node=mock.ANY),
                                      mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.END,
                                      mock.ANY, node=mock.ANY)])
        mock_sl.assert_called_once()
        mock_lg.assert_called_once()
        mock_ro.assert_called_once()
        mock_glu.assert_called_once()
        mock_rl.assert_called_once()
        mock_save.assert_called_once()
        self.assertEqual(lease.status, statuses.EXPIRED)

    @mock.patch('esi_leap.objects.lease.Lease.resource_object')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.get_lease_uuid')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.remove_lease')
    @mock.patch('esi_leap.objects.lease.Lease.save')
    @mock.patch('esi_leap.common.notification_utils'
                '._emit_notification')
    def test_expire_no_expire(self, mock_notify, mock_save, mock_rl,
                              mock_glu, mock_ro):
        lease = lease_obj.Lease(self.context, **self.test_lease_dict)
        test_node = TestNode('test-node', '12345')

        mock_ro.return_value = test_node
        mock_glu.return_value = 'some-other-lease-uuid'

        lease.expire()

        mock_notify.assert_has_calls([mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.START,
                                      mock.ANY, node=mock.ANY),
                                      mock.call(mock.ANY, mock.ANY, 'delete',
                                      obj_fields.NotificationLevel.INFO,
                                      obj_fields.NotificationStatus.END,
                                      mock.ANY, node=mock.ANY)])
        mock_ro.assert_called_once()
        mock_glu.assert_called_once()
        mock_rl.assert_not_called()
        mock_save.assert_called_once()
        self.assertEqual(lease.status, statuses.EXPIRED)

    def test_destroy(self):
        lease = lease_obj.Lease(self.context, **self.test_lease_dict)
        with mock.patch.object(self.db_api, 'lease_destroy',
                               autospec=True) as mock_lease_cancel:
            lease.destroy()
            mock_lease_cancel.assert_called_once_with(lease.uuid)

    def test_save(self):
        lease = lease_obj.Lease(self.context, **self.test_lease_dict)
        new_status = statuses.ACTIVE
        updated_at = datetime.datetime(2006, 12, 11, 0, 0)
        with mock.patch.object(self.db_api, 'lease_update',
                               autospec=True) as mock_lease_update:
            updated_lease = self.test_lease_dict.copy()
            updated_lease['status'] = new_status
            updated_lease['updated_at'] = updated_at
            mock_lease_update.return_value = updated_lease

            lease.status = new_status
            lease.save(self.context)

            updated_values = self.test_lease_dict.copy()
            updated_values['status'] = new_status
            mock_lease_update.assert_called_once_with(lease.uuid,
                                                      updated_values)
            self.assertEqual(self.context, lease._context)
            self.assertEqual(updated_at, lease.updated_at)

    @mock.patch('esi_leap.objects.lease.get_resource_object')
    def test_resource_object(self, mock_gro):
        lease = lease_obj.Lease(self.context, **self.test_lease_dict)
        lease.resource_object()
        mock_gro.assert_called_once_with(lease.resource_type,
                                         lease.resource_uuid)


class TestLeaseCRUDPayloads(base.DBTestCase):

    def setUp(self):
        super(TestLeaseCRUDPayloads, self).setUp()
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

    def test_lease_crud_payload(self):
        payload = lease_obj.LeaseCRUDPayload(self.lease, self.node)
        self.assertEqual(self.lease.id, payload.id)
        self.assertEqual(self.lease.name, payload.name)
        self.assertEqual(self.lease.start_time, payload.start_time)
        self.assertEqual(self.lease.end_time, payload.end_time)
        self.assertEqual(self.lease.fulfill_time, payload.fulfill_time)
        self.assertEqual(self.lease.expire_time, payload.expire_time)
        self.assertEqual(self.lease.uuid, payload.uuid)
        self.assertEqual(self.lease.resource_type, payload.resource_type)
        self.assertEqual(self.lease.resource_uuid, payload.resource_uuid)
        self.assertEqual(self.lease.project_id, payload.project_id)
        self.assertEqual(self.lease.owner_id, payload.owner_id)
        self.assertEqual(self.lease.parent_lease_uuid,
                         payload.parent_lease_uuid)
        self.assertEqual(self.lease.offer_uuid, payload.offer_uuid)
        self.assertEqual(self.lease.properties, payload.properties)
        self.assertEqual(self.lease.status, payload.status)
        self.assertEqual(self.lease.purpose, payload.purpose)
        self.assertEqual(self.node.node_name, payload.node_name)
        self.assertEqual(self.node._uuid, payload.node_uuid)
        self.assertEqual(self.node.node_power_state,
                         payload.node_power_state)
        self.assertEqual(self.node.node_provision_state,
                         payload.node_provision_state),
        self.assertEqual(self.node.node_properties,
                         payload.node_properties)
