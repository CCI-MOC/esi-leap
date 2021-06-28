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
from esi_leap.objects import lease as lease_obj
from esi_leap.objects import offer as offer_obj
from esi_leap.objects import owner_change
from esi_leap.resource_objects.test_node import TestNode
from esi_leap.tests import base


class TestOwnerChangeObject(base.DBTestCase):

    def setUp(self):
        super(TestOwnerChangeObject, self).setUp()

        self.now = datetime.datetime(2016, 7, 16, 19, 20, 30)
        self.test_node = TestNode('test-node', '12345')
        self.test_offer = offer_obj.Offer(
            resource_type='test_node',
            resource_uuid='12345',
            uuid=uuidutils.generate_uuid(),
            status=statuses.AVAILABLE,
            project_id='54321',
        )
        self.test_lease = lease_obj.Lease(
            uuid=uuidutils.generate_uuid(),
            resource_type='test_node',
            resource_uuid='11345',
            project_id='67890',
            owner_id='54321'
        )
        self.test_oc_data = {
            'id': 27,
            'uuid': uuidutils.generate_uuid(),
            'from_owner_id': 'owner1',
            'to_owner_id': 'owner2',
            'resource_type': 'test_node',
            'resource_uuid': '12345',
            'start_time': self.now,
            'end_time': self.now + datetime.timedelta(days=100),
            'fulfill_time': None,
            'expire_time': None,
            'status': statuses.ACTIVE,
            'created_at': None,
            'updated_at': None
        }
        self.config(lock_path=tempfile.mkdtemp(), group='oslo_concurrency')

    @mock.patch('esi_leap.db.sqlalchemy.api.owner_change_get_by_uuid')
    def test_get(self, mock_ocgbu):
        oc_uuid = self.test_oc_data['uuid']
        mock_ocgbu.return_value = self.test_oc_data

        oc = owner_change.OwnerChange.get(oc_uuid, self.context)

        mock_ocgbu.assert_called_once_with(oc_uuid)
        self.assertEqual(self.context, oc._context)

    @mock.patch('esi_leap.db.sqlalchemy.api.owner_change_get_all')
    def test_get_all(self, mock_ocga):
        mock_ocga.return_value = [self.test_oc_data]

        ocs = owner_change.OwnerChange.get_all({}, self.context)

        mock_ocga.assert_called_once_with({})
        self.assertEqual(len(ocs), 1)
        self.assertIsInstance(ocs[0], owner_change.OwnerChange)
        self.assertEqual(self.context, ocs[0]._context)

    @mock.patch('esi_leap.db.sqlalchemy.api.resource_verify_availability')
    @mock.patch('esi_leap.db.sqlalchemy.api.owner_change_create')
    def test_create(self, mock_occ, mock_rva):
        oc = owner_change.OwnerChange(self.context, **self.test_oc_data)
        mock_occ.return_value = self.test_oc_data

        oc.create(self.context)

        mock_rva.assert_called_once_with(oc.resource_type,
                                         oc.resource_uuid,
                                         oc.start_time,
                                         oc.end_time,
                                         is_owner_change=True)
        mock_occ.assert_called_once_with(self.test_oc_data)

    def test_create_invalid_time(self):
        bad_oc_data = {
            'id': 27,
            'uuid': '534653c9-880d-4c2d-6d6d-11111111111',
            'from_owner_id': 'owner1',
            'to_owner_id': 'owner2',
            'resource_type': 'test_node',
            'resource_uuid': '12345',
            'start_time': self.now + datetime.timedelta(days=100),
            'end_time': self.now,
            'status': statuses.CREATED,
            'created_at': None,
            'updated_at': None
        }

        oc = owner_change.OwnerChange(self.context, **bad_oc_data)

        self.assertRaises(exception.InvalidTimeRange, oc.create)

    @mock.patch('esi_leap.db.sqlalchemy.api.resource_verify_availability')
    @mock.patch('esi_leap.db.sqlalchemy.api.owner_change_create')
    def test_create_concurrent(self, mock_occ, mock_rva):
        oc = owner_change.OwnerChange(self.context, **self.test_oc_data)
        oc2 = owner_change.OwnerChange(self.context, **self.test_oc_data)
        oc2.id = 28

        def create_mock(updates):
            mock_rva.side_effect = Exception("bad")

        mock_occ.side_effect = create_mock

        thread = threading.Thread(target=oc.create)
        thread2 = threading.Thread(target=oc2.create)

        thread.start()
        thread2.start()

        thread.join()
        thread2.join()

        assert mock_rva.call_count == 2
        mock_occ.assert_called_once()

    @mock.patch('esi_leap.db.sqlalchemy.api.owner_change_destroy')
    def test_destroy(self, mock_ocd):
        oc = owner_change.OwnerChange(self.context, **self.test_oc_data)
        oc.destroy()
        mock_ocd.assert_called_once_with(oc.uuid)

    @mock.patch('esi_leap.db.sqlalchemy.api.owner_change_update')
    def test_save(self, mock_ocu):
        oc = owner_change.OwnerChange(self.context, **self.test_oc_data)
        new_status = statuses.DELETED
        updated_at = datetime.datetime(2006, 12, 11, 0, 0)

        updated_oc = self.test_oc_data.copy()
        updated_oc['status'] = new_status
        updated_oc['updated_at'] = updated_at
        mock_ocu.return_value = updated_oc

        oc.status = new_status
        oc.save(self.context)

        updated_values = self.test_oc_data.copy()
        updated_values['status'] = new_status
        mock_ocu.assert_called_once_with(oc.uuid, updated_values)
        self.assertEqual(self.context, oc._context)
        self.assertEqual(updated_at, oc.updated_at)

    @mock.patch('esi_leap.resource_objects.test_node.TestNode.set_owner')
    @mock.patch('esi_leap.db.sqlalchemy.api.owner_change_update')
    def test_fulfill(self, mock_ocu, mock_so):
        oc_fulfill_data = self.test_oc_data.copy()
        oc_fulfill_data['status'] = statuses.ACTIVE
        mock_ocu.return_value = oc_fulfill_data

        oc = owner_change.OwnerChange(self.context, **self.test_oc_data)
        oc.fulfill()

        mock_so.assert_called_once_with(oc.to_owner_id)
        mock_ocu.assert_called_once

    @mock.patch('esi_leap.objects.lease.Lease.cancel')
    @mock.patch('esi_leap.objects.owner_change.OwnerChange.leases')
    @mock.patch('esi_leap.objects.offer.Offer.cancel')
    @mock.patch('esi_leap.objects.owner_change.OwnerChange.offers')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.set_owner')
    @mock.patch('esi_leap.db.sqlalchemy.api.owner_change_update')
    def test_cancel(self, mock_ocu, mock_so, mock_offers, mock_oc,
                    mock_leases, mock_lc):
        mock_offers.return_value = [self.test_offer, self.test_offer]
        mock_leases.return_value = [self.test_lease, self.test_lease]
        oc_cancel_data = self.test_oc_data.copy()
        oc_cancel_data['status'] = statuses.DELETED
        mock_ocu.return_value = oc_cancel_data

        oc = owner_change.OwnerChange(self.context, **self.test_oc_data)
        oc.cancel()

        mock_offers.assert_called_once
        assert mock_oc.call_count == 2
        mock_leases.assert_called_once
        assert mock_lc.call_count == 2
        mock_so.assert_called_once_with(oc.from_owner_id)
        mock_ocu.assert_called_once

    @mock.patch('esi_leap.objects.lease.Lease.cancel')
    @mock.patch('esi_leap.objects.owner_change.OwnerChange.leases')
    @mock.patch('esi_leap.objects.offer.Offer.cancel')
    @mock.patch('esi_leap.objects.owner_change.OwnerChange.offers')
    @mock.patch('esi_leap.resource_objects.test_node.TestNode.set_owner')
    @mock.patch('esi_leap.db.sqlalchemy.api.owner_change_update')
    def test_expire(self, mock_ocu, mock_so, mock_offers, mock_oc,
                    mock_leases, mock_lc):
        mock_offers.return_value = [self.test_offer, self.test_offer]
        mock_leases.return_value = [self.test_lease, self.test_lease]
        oc_expire_data = self.test_oc_data.copy()
        oc_expire_data['status'] = statuses.EXPIRED
        mock_ocu.return_value = oc_expire_data

        oc = owner_change.OwnerChange(self.context, **self.test_oc_data)
        oc.expire()

        mock_offers.assert_called_once
        assert mock_oc.call_count == 2
        mock_leases.assert_called_once
        assert mock_lc.call_count == 2
        mock_so.assert_called_once_with(oc.from_owner_id)
        mock_ocu.assert_called_once

    @mock.patch('esi_leap.db.sqlalchemy.api.offer_get_all')
    def test_offers(self, mock_oga):
        oc = owner_change.OwnerChange(self.context, **self.test_oc_data)
        oc.offers()

        expected_filters = {
            'project_id': oc.to_owner_id,
            'start_time': oc.start_time,
            'end_time': oc.end_time,
            'time_filter_type': 'within',
            'status': statuses.AVAILABLE
        }
        mock_oga.assert_called_once_with(expected_filters)

    @mock.patch('esi_leap.db.sqlalchemy.api.lease_get_all')
    def test_leases(self, mock_lga):
        oc = owner_change.OwnerChange(self.context, **self.test_oc_data)
        oc.leases()

        expected_filters = {
            'owner_id': oc.to_owner_id,
            'start_time': oc.start_time,
            'end_time': oc.end_time,
            'time_filter_type': 'within',
            'status': [statuses.CREATED, statuses.ACTIVE]
        }
        mock_lga.assert_called_once_with(expected_filters)

    @mock.patch('esi_leap.resource_objects.resource_object_factory.'
                'ResourceObjectFactory.get_resource_object')
    def test_resource_object(self, mock_gro):
        oc = owner_change.OwnerChange(self.context, **self.test_oc_data)
        oc.resource_object()
        mock_gro.assert_called_once_with(oc.resource_type, oc.resource_uuid)
