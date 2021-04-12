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
from esi_leap.tests import base


start = datetime.datetime(2016, 7, 16, 19, 20, 30)

o_uuid = uuidutils.generate_uuid()
c_uuid = uuidutils.generate_uuid()
c_uuid_2 = uuidutils.generate_uuid()
c_uuid_3 = uuidutils.generate_uuid()
c_uuid_4 = uuidutils.generate_uuid()


def get_test_lease_1():
    return {
        'id': 27,
        'name': 'c',
        'uuid': c_uuid,
        'project_id': 'le55ee',
        'start_time': start + datetime.timedelta(days=5),
        'end_time': start + datetime.timedelta(days=10),
        'fulfill_time': start + datetime.timedelta(days=5),
        'expire_time': start + datetime.timedelta(days=10),
        'status': statuses.CREATED,
        'properties': {},
        'offer_uuid': o_uuid,
        'created_at': None,
        'updated_at': None
    }


def get_test_lease_2():

    return {
        'id': 28,
        'name': 'c',
        'uuid': c_uuid_2,
        'project_id': 'le55ee',
        'start_time': start + datetime.timedelta(days=15),
        'end_time': start + datetime.timedelta(days=20),
        'fulfill_time': start + datetime.timedelta(days=15),
        'expire_time': start + datetime.timedelta(days=20),
        'status': statuses.CREATED,
        'properties': {},
        'offer_uuid': o_uuid,
        'created_at': None,
        'updated_at': None
    }


def get_test_lease_3():

    return {
        'id': 29,
        'name': 'c',
        'uuid': c_uuid_3,
        'project_id': 'le55ee_2',
        'start_time': start + datetime.timedelta(days=25),
        'end_time': start + datetime.timedelta(days=30),
        'fulfill_time': start + datetime.timedelta(days=25),
        'expire_time': start + datetime.timedelta(days=30),
        'status': statuses.CREATED,
        'properties': {},
        'offer_uuid': o_uuid,
        'created_at': None,
        'updated_at': None
    }


def get_test_lease_4():

    return {
        'id': 30,
        'name': 'l2',
        'uuid': c_uuid_4,
        'project_id': 'le55ee_2',
        'start_time': start + datetime.timedelta(days=35),
        'end_time': start + datetime.timedelta(days=40),
        'fulfill_time': start + datetime.timedelta(days=35),
        'expire_time': start + datetime.timedelta(days=40),
        'status': statuses.CREATED,
        'properties': {},
        'offer_uuid': o_uuid,
        'created_at': None,
        'updated_at': None
    }


def get_offer():

    class Offer(object):
        pass

    o = Offer()
    offer = dict(
        id=27,
        uuid=o_uuid,
        project_id='01d4e6a72f5c408813e02f664cc8c83e',
        resource_type='dummy_node',
        resource_uuid='1718',
        start_time=start,
        end_time=start + datetime.timedelta(days=100),
        status=statuses.AVAILABLE,
        properties={'floor_price': 3},
        created_at=None,
        updated_at=None
    )

    for k, v in offer.items():
        setattr(o, k, v)

    return o


class TestLeaseObject(base.DBTestCase):

    def setUp(self):
        super(TestLeaseObject, self).setUp()
        self.fake_lease = get_test_lease_1()
        self.fake_lease_2 = get_test_lease_2()
        self.fake_lease_3 = get_test_lease_3()
        self.fake_lease_4 = get_test_lease_4()

        self.config(lock_path=tempfile.mkdtemp(), group='oslo_concurrency')

    def test_get(self):
        lease_uuid = self.fake_lease['uuid']
        with mock.patch.object(self.db_api, 'lease_get_by_uuid',
                               autospec=True) as mock_lease_get_by_uuid:
            mock_lease_get_by_uuid.return_value = self.fake_lease

            lease = lease_obj.Lease.get(lease_uuid, self.context)

            mock_lease_get_by_uuid.assert_called_once_with(
                lease_uuid)
            self.assertEqual(self.context, lease._context)

    def test_get_all(self):
        with mock.patch.object(
                self.db_api, 'lease_get_all', autospec=True
        ) as mock_lease_get_all:
            mock_lease_get_all.return_value = \
                [self.fake_lease, self.fake_lease_2,
                 self.fake_lease_3, self.fake_lease_4]

            leases = lease_obj.Lease.get_all(
                {}, self.context)

            mock_lease_get_all.assert_called_once_with({})
            self.assertEqual(len(leases), 4)
            self.assertIsInstance(
                leases[0], lease_obj.Lease)
            self.assertEqual(self.context, leases[0]._context)

    def test_create(self):
        lease = lease_obj.Lease(
            self.context, **self.fake_lease)
        with mock.patch.object(self.db_api, 'lease_create',
                               autospec=True) as mock_lease_create:
            with mock.patch.object(self.db_api, 'offer_get_by_uuid',
                                   autospec=True) as mock_offer_get:
                with mock.patch.object(self.db_api,
                                       'offer_verify_lease_availability',
                                       autospec=True):

                    mock_lease_create.return_value = get_test_lease_1()
                    mock_offer_get.return_value = get_offer()

                    lease.create()

                    mock_lease_create.assert_called_once_with(
                        get_test_lease_1())
                    mock_offer_get.assert_called_once()

    def test_create_invalid_time(self):
        bad_lease = {
            'id': 30,
            'name': 'l2',
            'uuid': '534653c9-880d-4c2d-6d6d-44444444444',
            'project_id': 'le55ee_2',
            'start_time': start + datetime.timedelta(days=30),
            'end_time': start + datetime.timedelta(days=20),
            'fulfill_time': start + datetime.timedelta(days=35),
            'expire_time': start + datetime.timedelta(days=40),
            'status': statuses.CREATED,
            'properties': {},
            'offer_uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
            'created_at': None,
            'updated_at': None
        }

        lease = lease_obj.Lease(self.context, **bad_lease)

        self.assertRaises(exception.InvalidTimeRange, lease.create)

    def test_create_concurrent(self):
        lease = lease_obj.Lease(
            self.context, **self.fake_lease)

        lease2 = lease_obj.Lease(
            self.context, **self.fake_lease)

        lease2.id = 28

        offer = get_offer()

        with mock.patch.object(self.db_api, 'lease_create',
                               autospec=True) as mock_lease_create:
            with mock.patch.object(self.db_api, 'offer_get_by_uuid',
                                   autospec=True) as mock_offer_get:
                with mock.patch.object(self.db_api,
                                       'offer_verify_lease_availability',
                                       autospec=True) as mock_ovca:

                    mock_offer_get.return_value = offer

                    def update_mock(updates):
                        mock_ovca.side_effect = Exception("bad")

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

    def test_destroy(self):
        lease = lease_obj.Lease(self.context, **self.fake_lease)
        with mock.patch.object(self.db_api, 'lease_destroy',
                               autospec=True) as mock_lease_cancel:

            lease.destroy()

            mock_lease_cancel.assert_called_once_with(
                lease.uuid)

    def test_save(self):
        lease = lease_obj.Lease(self.context, **self.fake_lease)
        new_status = statuses.ACTIVE
        updated_at = datetime.datetime(2006, 12, 11, 0, 0)
        with mock.patch.object(self.db_api, 'lease_update',
                               autospec=True) as mock_lease_update:
            updated_lease = get_test_lease_1()
            updated_lease['status'] = new_status
            updated_lease['updated_at'] = updated_at
            mock_lease_update.return_value = updated_lease

            lease.status = new_status
            lease.save(self.context)

            updated_values = get_test_lease_1()
            updated_values['status'] = new_status
            mock_lease_update.assert_called_once_with(
                lease.uuid, updated_values)
            self.assertEqual(self.context, lease._context)
            self.assertEqual(updated_at, lease.updated_at)
