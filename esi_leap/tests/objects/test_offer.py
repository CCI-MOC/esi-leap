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
from esi_leap.objects import offer
from esi_leap.tests import base

start = datetime.datetime(2016, 7, 16, 19, 20, 30)

o_uuid = uuidutils.generate_uuid()
o_uuid_2 = uuidutils.generate_uuid()
o_uuid_3 = uuidutils.generate_uuid()


def get_test_offer():

    return {
        'id': 27,
        'name': "o",
        'uuid': o_uuid,
        'project_id': '0wn5r',
        'resource_type': 'dummy_node',
        'resource_uuid': '1718',
        'start_time': start,
        'end_time': start + datetime.timedelta(days=100),
        'status': statuses.AVAILABLE,
        'properties': {'floor_price': 3},
        'created_at': None,
        'updated_at': None
    }


def get_test_offer_2():

    return {
        'id': 28,
        'name': "o",
        'uuid': o_uuid_2,
        'project_id': '0wn5r',
        'resource_type': 'dummy_node',
        'resource_uuid': '1718',
        'start_time': start,
        'end_time': start + datetime.timedelta(days=100),
        'status': statuses.AVAILABLE,
        'properties': {'floor_price': 3},
        'created_at': None,
        'updated_at': None
    }


def get_test_offer_3():

    return {
        'id': 29,
        'name': "o",
        'uuid': o_uuid_3,
        'project_id': '0wn5r2',
        'resource_type': 'dummy_node',
        'resource_uuid': '1718',
        'start_time': start,
        'end_time': start + datetime.timedelta(days=100),
        'status': statuses.AVAILABLE,
        'properties': {'floor_price': 3},
        'created_at': None,
        'updated_at': None
    }


class TestOfferObject(base.DBTestCase):

    def setUp(self):
        super(TestOfferObject, self).setUp()
        self.fake_offer = get_test_offer()
        self.fake_offer_2 = get_test_offer_2()
        self.fake_offer_3 = get_test_offer_3()

        self.config(lock_path=tempfile.mkdtemp(), group='oslo_concurrency')

    def test_get(self):
        offer_uuid = self.fake_offer['uuid']
        with mock.patch.object(self.db_api, 'offer_get_by_uuid',
                               autospec=True) as mock_offer_get_by_uuid:
            mock_offer_get_by_uuid.return_value = self.fake_offer

            c = offer.Offer.get(offer_uuid, self.context)

            mock_offer_get_by_uuid.assert_called_once_with(
                offer_uuid)
            self.assertEqual(self.context, c._context)

    def test_get_all(self):
        with mock.patch.object(
                self.db_api, 'offer_get_all', autospec=True
        ) as mock_offer_get_all:
            mock_offer_get_all.return_value = [
                self.fake_offer]

            offers = offer.Offer.get_all(
                {}, self.context)

            mock_offer_get_all.assert_called_once_with(
                {})
            self.assertEqual(len(offers), 1)
            self.assertIsInstance(
                offers[0], offer.Offer)
            self.assertEqual(self.context, offers[0]._context)

    def test_get_availabilities(self):
        o = offer.Offer(
            self.context, **self.fake_offer)
        with mock.patch.object(
                self.db_api, 'offer_get_conflict_times', autospec=True
        ) as mock_offer_get_conflict_times:
            mock_offer_get_conflict_times.return_value = [
                [
                    o.start_time + datetime.timedelta(days=10),
                    o.start_time + datetime.timedelta(days=20)
                ],
                [
                    o.start_time + datetime.timedelta(days=20),
                    o.start_time + datetime.timedelta(days=30)
                ],
                [
                    o.start_time + datetime.timedelta(days=50),
                    o.start_time + datetime.timedelta(days=60)
                ]
            ]

            expect = [
                [
                    o.start_time,
                    o.start_time + datetime.timedelta(days=10)
                ],
                [
                    o.start_time + datetime.timedelta(days=30),
                    o.start_time + datetime.timedelta(days=50)
                ],
                [
                    o.start_time + datetime.timedelta(days=60),
                    o.end_time
                ],
            ]
            a = o.get_availabilities()
            self.assertEqual(a, expect)

            mock_offer_get_conflict_times.return_value = [
                [
                    o.start_time,
                    o.end_time
                ],
            ]

            expect = []
            a = o.get_availabilities()
            self.assertEqual(a, expect)

            mock_offer_get_conflict_times.return_value = []

            expect = [
                [
                    o.start_time,
                    o.end_time
                ],
            ]
            a = o.get_availabilities()
            self.assertEqual(a, expect)

    def test_create(self):
        o = offer.Offer(
            self.context, **self.fake_offer)
        with mock.patch.object(self.db_api, 'offer_create',
                               autospec=True) as mock_offer_create:

            mock_offer_create.return_value = get_test_offer()

            o.create(self.context)
            mock_offer_create.assert_called_once_with(get_test_offer())

    def test_create_invalid_time(self):

        bad_offer = {
            'id': 27,
            'name': "o",
            'uuid': '534653c9-880d-4c2d-6d6d-11111111111',
            'project_id': '0wn5r',
            'resource_type': 'dummy_node',
            'resource_uuid': '1718',
            'start_time': start + datetime.timedelta(days=100),
            'end_time': start,
            'status': statuses.AVAILABLE,
            'properties': {'floor_price': 3},
            'created_at': None,
            'updated_at': None
        }

        o = offer.Offer(
            self.context, **bad_offer)

        self.assertRaises(exception.InvalidTimeRange, o.create)

    def test_create_concurrent(self):
        o = offer.Offer(
            self.context, **self.fake_offer)

        o2 = offer.Offer(
            self.context, **self.fake_offer)

        o2.id = 28

        with mock.patch.object(self.db_api, 'offer_create',
                               autospec=True) as mock_offer_create:
            with mock.patch.object(self.db_api,
                                   'offer_verify_resource_availability',
                                   autospec=True) as mock_ovra:

                def update_mock(updates):
                    mock_ovra.side_effect = Exception("bad")

                mock_offer_create.side_effect = update_mock

                thread = threading.Thread(target=o.create)
                thread2 = threading.Thread(target=o2.create)

                thread.start()
                thread2.start()

                thread.join()
                thread2.join()

                assert mock_ovra.call_count == 2
                mock_offer_create.assert_called_once()

    def test_destroy(self):
        o = offer.Offer(self.context, **self.fake_offer)
        with mock.patch.object(self.db_api, 'offer_destroy',
                               autospec=True) as mock_offer_cancel:

            o.destroy()

            mock_offer_cancel.assert_called_once_with(
                o.uuid)

    def test_save(self):
        o = offer.Offer(self.context, **self.fake_offer)
        new_status = statuses.CANCELLED
        updated_at = datetime.datetime(2006, 12, 11, 0, 0)
        with mock.patch.object(self.db_api, 'offer_update',
                               autospec=True) as mock_offer_update:
            updated_offer = get_test_offer()
            updated_offer['status'] = new_status
            updated_offer['updated_at'] = updated_at
            mock_offer_update.return_value = updated_offer

            o.status = new_status
            o.save(self.context)

            updated_values = get_test_offer()
            updated_values['status'] = new_status
            mock_offer_update.assert_called_once_with(
                o.uuid, updated_values)
            self.assertEqual(self.context, o._context)
            self.assertEqual(updated_at, o.updated_at)
