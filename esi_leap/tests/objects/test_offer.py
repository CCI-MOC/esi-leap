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

from esi_leap.common import statuses
from esi_leap.objects import offer
from esi_leap.tests import base

start = datetime.datetime(2016, 7, 16, 19, 20, 30)


def get_test_offer():

    return {
        'id': 27,
        'name': "o",
        'uuid': '534653c9-880d-4c2d-6d6d-11111111111',
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
        'uuid': '534653c9-880d-4c2d-6d6d-2222222222',
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
        'uuid': '534653c9-880d-4c2d-6d6d-3333333333',
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

    def test_get_by_uuid(self):
        offer_uuid = self.fake_offer['uuid']
        with mock.patch.object(self.db_api, 'offer_get_by_uuid',
                               autospec=True) as mock_offer_get_by_uuid:
            mock_offer_get_by_uuid.return_value = self.fake_offer

            c = offer.Offer.get_by_uuid(
                offer_uuid, self.context)

            mock_offer_get_by_uuid.assert_called_once_with(
                offer_uuid)
            self.assertEqual(self.context, c._context)

    def test_get_by_name(self):
        with mock.patch.object(self.db_api, 'offer_get_by_name',
                               autospec=True) as mock_offer_get_by_name:
            mock_offer_get_by_name.return_value = \
                [self.fake_offer, self.fake_offer_2,
                 self.fake_offer_3]

            o = offer.Offer.get_by_name(
                'o', self.context)

            mock_offer_get_by_name.assert_called_once_with('o')
            self.assertEqual(self.context, o[0]._context)

    def test_get(self):
        with mock.patch.object(self.db_api, 'offer_get_by_name',
                               autospec=True) as mock_offer_get_by_name:
            with mock.patch.object(self.db_api, 'offer_get_by_uuid',
                                   autospec=True) as mock_offer_get_by_uuid:

                mock_offer_get_by_name.return_value = \
                    [self.fake_offer, self.fake_offer_2,
                     self.fake_offer_3]
                mock_offer_get_by_uuid.return_value = None

                o = offer.Offer.get(
                    'o', self.context)

                mock_offer_get_by_uuid.assert_called_once_with('o')
                mock_offer_get_by_name.assert_called_once_with('o')
                assert len(o) == 3

        with mock.patch.object(self.db_api, 'offer_get_by_name',
                               autospec=True) as mock_offer_get_by_name:
            with mock.patch.object(self.db_api, 'offer_get_by_uuid',
                                   autospec=True) as mock_offer_get_by_uuid:

                mock_offer_get_by_uuid.return_value = self.fake_offer
                o = offer.Offer.get(
                    self.fake_offer['uuid'], self.context)

                mock_offer_get_by_uuid.assert_called_once_with(
                    self.fake_offer['uuid']
                )
                assert not mock_offer_get_by_name.called
                assert len(o) == 1

    def test_get_all(self):
        with mock.patch.object(
                self.db_api, 'offer_get_all', autospec=True
        ) as mock_offer_get_all:
            mock_offer_get_all.return_value = [
                self.fake_offer]

            offers = offer.Offer.get_all(
                self.context, {})

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
            with mock.patch(
                    'esi_leap.objects.offer.uuidutils.generate_uuid') \
                    as mock_uuid:
                mock_uuid.return_value = '534653c9-880d-4c2d-6d6d-' \
                                         '11111111111'
                mock_offer_create.return_value = get_test_offer()

                o.create(self.context)
                mock_offer_create.assert_called_once_with(
                    get_test_offer())

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
