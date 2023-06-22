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

from esi_leap.common import exception as e
from esi_leap.common import statuses
from esi_leap.db.sqlalchemy import api
import esi_leap.tests.base as base

now = datetime.datetime(2016, 7, 16, 19, 20, 30)

test_offer_1 = dict(
    uuid='11111',
    project_id='0wn3r',
    name='o1',
    resource_uuid='1111',
    resource_type='dummy_node',
    start_time=now,
    end_time=now + datetime.timedelta(days=100),
    properties={'foo': 'bar'},
    status=statuses.AVAILABLE,
)

test_offer_2 = dict(
    uuid='22222',
    project_id='0wn3r',
    lessee_id='12345',
    name='o1',
    resource_uuid='1111',
    resource_type='dummy_node',
    start_time=now + datetime.timedelta(days=25),
    end_time=now + datetime.timedelta(days=100),
    properties={'foo': 'bar'},
    status=statuses.AVAILABLE,
)

test_offer_3 = dict(
    uuid='33333',
    project_id='0wn3r_2',
    lessee_id='67890',
    name='o1',
    resource_uuid='1111',
    resource_type='dummy_node',
    start_time=now + datetime.timedelta(days=50),
    end_time=now + datetime.timedelta(days=100),
    properties={'foo': 'bar'},
    status=statuses.AVAILABLE,
)

test_offer_4 = dict(
    uuid='44444',
    project_id='0wn3r_2',
    lessee_id='ABCDE',
    name='o2',
    resource_uuid='1111',
    resource_type='dummy_node',
    start_time=now + datetime.timedelta(days=75),
    end_time=now + datetime.timedelta(days=100),
    properties={'foo': 'bar'},
    status=statuses.AVAILABLE,
)

test_offer_5 = dict(
    uuid='55555',
    project_id='12345',
    lessee_id='ABCDE',
    name='o2',
    resource_uuid='1111',
    resource_type='dummy_node',
    start_time=now + datetime.timedelta(days=105),
    end_time=now + datetime.timedelta(days=150),
    properties={'foo': 'bar'},
    status=statuses.AVAILABLE,
)

test_lease_1 = dict(
    uuid='11111',
    project_id='1e5533',
    owner_id='0wn3r',
    name='l1',
    resource_uuid='1111',
    resource_type='dummy_node',
    purpose='test_purpose',
    start_time=now + datetime.timedelta(days=10),
    end_time=now + datetime.timedelta(days=20),
    properties={},
    status=statuses.CREATED,
)

test_lease_2 = dict(
    uuid='22222',
    project_id='1e5533',
    owner_id='0wn3r',
    name='l1',
    resource_uuid='1111',
    resource_type='dummy_node',
    purpose='test_purpose',
    start_time=now + datetime.timedelta(days=20),
    end_time=now + datetime.timedelta(days=30),
    properties={},
    status=statuses.CREATED,
)

test_lease_3 = dict(
    uuid='33333',
    project_id='1e5533_2',
    owner_id='0wn3r_2',
    name='l1',
    resource_uuid='1111',
    resource_type='dummy_node',
    purpose='test_purpose',
    start_time=now + datetime.timedelta(days=50),
    end_time=now + datetime.timedelta(days=60),
    properties={},
    status=statuses.ACTIVE,
)

test_lease_4 = dict(
    uuid='44444',
    project_id='1e5533_2',
    owner_id='0wn3r_2',
    name='l4',
    resource_uuid='1111',
    resource_type='dummy_node',
    purpose='test_purpose',
    start_time=now + datetime.timedelta(days=85),
    end_time=now + datetime.timedelta(days=90),
    properties={},
    status=statuses.DELETED,
)

test_lease_5 = dict(
    project_id='0wn3r',
    owner_id='0wn3r_2',
    name='l5',
    resource_uuid='1111',
    resource_type='dummy_node',
    purpose='test_purpose',
    start_time=now + datetime.timedelta(days=90),
    end_time=now + datetime.timedelta(days=100),
    uuid='55555',
    properties={},
    status=statuses.EXPIRED,
)

test_lease_6 = dict(
    project_id='0wn3r',
    owner_id='0wn3r_2',
    name='l6',
    resource_uuid='2222',
    resource_type='dummy_node',
    purpose='test_purpose',
    start_time=now + datetime.timedelta(days=5),
    end_time=now + datetime.timedelta(days=30),
    uuid='6666',
    properties={},
    status=statuses.EXPIRED,
)

test_event_1 = dict(
    id=1,
    event_type='fake:event:start',
    event_time=now - datetime.timedelta(days=20),
    object_type='lease',
    object_uuid='11111',
    resource_type='dummy_node',
    resource_uuid='1111',
    lessee_id='1e5533',
    owner_id='0wn3r',
)

test_event_2 = dict(
    id=2,
    event_type='fake:event:end',
    event_time=now - datetime.timedelta(days=10),
    object_type='lease',
    object_uuid='11111',
    resource_type='dummy_node',
    resource_uuid='1111',
    lessee_id='1e5533',
    owner_id='0wn3r',
)

test_event_3 = dict(
    id=3,
    event_type='fake:event:start',
    event_time=now - datetime.timedelta(days=20),
    object_type='lease',
    object_uuid='22222',
    resource_type='dummy_node',
    resource_uuid='2222',
    lessee_id='1e5533',
    owner_id='0wn3r2',
)


class TestOfferAPI(base.DBTestCase):

    def test_offer_create(self):
        offer = api.offer_create(test_offer_1)
        o = api.offer_get_all({}).all()
        assert len(o) == 1
        assert o[0].to_dict() == offer.to_dict()

    def test_offer_verify_availability(self):
        offer = api.offer_create(test_offer_1)

        test_lease_1['offer_uuid'] = offer.uuid
        test_lease_2['offer_uuid'] = offer.uuid
        test_lease_3['offer_uuid'] = offer.uuid

        api.lease_create(test_lease_1)
        api.lease_create(test_lease_2)
        api.lease_create(test_lease_3)

        start = now + datetime.timedelta(days=35)
        end = now + datetime.timedelta(days=40)
        api.offer_verify_availability(offer, start, end)

        start = now + datetime.timedelta(days=5)
        end = now + datetime.timedelta(days=10)
        api.offer_verify_availability(offer, start, end)

        start = now
        end = now + datetime.timedelta(days=10)
        api.offer_verify_availability(offer, start, end)

        start = now + datetime.timedelta(days=90)
        end = now + datetime.timedelta(days=100)
        api.offer_verify_availability(offer, start, end)

        start = now + datetime.timedelta(days=60)
        end = now + datetime.timedelta(days=100)
        api.offer_verify_availability(offer, start, end)

        start = now + datetime.timedelta(days=30)
        end = now + datetime.timedelta(days=50)
        api.offer_verify_availability(offer, start, end)

        start = now + datetime.timedelta(days=15)
        end = now + datetime.timedelta(days=16)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=45)
        end = now + datetime.timedelta(days=55)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=55)
        end = now + datetime.timedelta(days=65)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=50)
        end = now + datetime.timedelta(days=65)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=45)
        end = now + datetime.timedelta(days=60)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=90)
        end = now + datetime.timedelta(days=105)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=100)
        end = now + datetime.timedelta(days=105)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=105)
        end = now + datetime.timedelta(days=110)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_availability,
                          offer, start, end)

        start = now - datetime.timedelta(days=1)
        end = now + datetime.timedelta(days=5)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_availability,
                          offer, start, end)

        start = now - datetime.timedelta(days=1)
        end = now
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_availability,
                          offer, start, end)

        start = now - datetime.timedelta(days=10)
        end = now - datetime.timedelta(days=5)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=45)
        end = now + datetime.timedelta(days=55)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_availability,
                          offer, start, end)

        test_lease_4['offer_uuid'] = offer.uuid
        api.lease_create(test_lease_4)
        start = now + datetime.timedelta(days=86)
        end = now + datetime.timedelta(days=87)
        api.offer_verify_availability(offer, start, end)

    def test_offer_get_conflict_times(self):
        o1 = api.offer_create(test_offer_1)
        self.assertEqual(api.offer_get_conflict_times(o1), [])
        test_lease_3['offer_uuid'] = o1.uuid
        test_lease_4['offer_uuid'] = o1.uuid
        test_lease_5['offer_uuid'] = o1.uuid
        api.lease_create(test_lease_3)
        api.lease_create(test_lease_4)
        api.lease_create(test_lease_5)
        self.assertEqual(api.offer_get_conflict_times(o1),
                         [(now + datetime.timedelta(days=50),
                          now + datetime.timedelta(days=60))])

    def test_offer_get_first_availability(self):
        o1 = api.offer_create(test_offer_1)
        self.assertEqual(api.offer_get_first_availability
                         (o1.uuid, o1.start_time,), None)
        test_lease_3['offer_uuid'] = o1.uuid
        api.lease_create(test_lease_3)
        self.assertEqual(api.offer_get_first_availability(o1.uuid,
                                                          o1.start_time),
                         (now + datetime.timedelta(days=50),))

    def test_offer_get_by_uuid(self):
        o1 = api.offer_create(test_offer_1)
        res = api.offer_get_by_uuid(o1.uuid)
        self.assertEqual(o1.uuid, res.uuid)
        self.assertEqual(o1.project_id, res.project_id)
        self.assertEqual(o1.properties, res.properties)

    def test_offer_get_by_uuid_not_found(self):
        assert api.offer_get_by_uuid('some_uuid') is None

    def test_offer_get_by_name(self):
        o1 = api.offer_create(test_offer_1)
        o2 = api.offer_create(test_offer_2)
        o3 = api.offer_create(test_offer_3)
        api.offer_create(test_offer_4)

        res = api.offer_get_by_name('o1')
        assert len(res) == 3
        self.assertEqual(o1.uuid, res[0].uuid)
        self.assertEqual(o1.project_id, res[0].project_id)

        self.assertEqual(o2.uuid, res[1].uuid)
        self.assertEqual(o2.project_id, res[1].project_id)

        self.assertEqual(o3.uuid, res[2].uuid)
        self.assertEqual(o3.project_id, res[2].project_id)

    def test_offer_get_by_name_not_found(self):
        self.assertEqual(api.offer_get_by_name('some_name'), [])

    def test_offer_destroy(self):
        o1 = api.offer_create(test_offer_2)
        api.offer_destroy(o1.uuid)
        self.assertEqual(api.offer_get_by_uuid('offer_2'), None)

    def test_offer_destroy_not_found(self):
        self.assertEqual(api.offer_get_by_uuid('offer_4'), None)

    def test_offer_update(self):
        o1 = api.offer_create(test_offer_3)
        values = {'start_time': test_offer_2['start_time'],
                  'end_time': test_offer_2['end_time']}
        api.offer_update(o1.uuid, values)
        o1 = api.offer_get_by_uuid(o1.uuid)

        self.assertEqual(test_offer_2['start_time'], o1.start_time)
        self.assertEqual(test_offer_2['end_time'], o1.end_time)

    def test_offer_update_invalid_time(self):
        o1 = api.offer_create(test_offer_3)
        values = {'start_time': now + datetime.timedelta(days=101),
                  'end_time': now}
        self.assertRaises(e.InvalidTimeRange, api.offer_update,
                          o1.uuid, values)

    def test_offer_get_all(self):
        o1 = api.offer_create(test_offer_2)
        o2 = api.offer_create(test_offer_3)
        res = api.offer_get_all({})

        self.assertEqual(2, res.count())
        self.assertEqual((o1.to_dict(), o2.to_dict()),
                         (res[0].to_dict(), res[1].to_dict()))

    @mock.patch('esi_leap.common.keystone.get_parent_project_id_tree')
    def test_offer_get_all_lessee_filter(self, mock_gppit):
        mock_gppit.return_value = ['12345', '67890']

        o1 = api.offer_create(test_offer_1)
        o2 = api.offer_create(test_offer_2)
        o3 = api.offer_create(test_offer_3)
        api.offer_create(test_offer_4)
        o5 = api.offer_create(test_offer_5)
        res = api.offer_get_all({'lessee_id': '12345'})

        mock_gppit.assert_called_once_with('12345')
        self.assertEqual(4, res.count())
        self.assertEqual((o1.to_dict(), o2.to_dict(), o3.to_dict(),
                          o5.to_dict()),
                         (res[0].to_dict(), res[1].to_dict(),
                          res[2].to_dict(), res[3].to_dict()))

    def test_offer_get_all_time_filter(self):
        o1 = api.offer_create(test_offer_1)
        o2 = api.offer_create(test_offer_2)
        api.offer_create(test_offer_3)
        api.offer_create(test_offer_4)
        api.offer_create(test_offer_5)
        res = api.offer_get_all({
            'start_time': o1.start_time + datetime.timedelta(days=26),
            'end_time': o1.end_time + datetime.timedelta(days=-1),
        })

        self.assertEqual(2, res.count())
        self.assertEqual((o1.to_dict(), o2.to_dict()),
                         (res[0].to_dict(), res[1].to_dict()))

    def test_offer_get_all_time_filter_within(self):
        o1 = api.offer_create(test_offer_1)
        o2 = api.offer_create(test_offer_2)
        o3 = api.offer_create(test_offer_3)
        o4 = api.offer_create(test_offer_4)
        api.offer_create(test_offer_5)
        res = api.offer_get_all({
            'start_time': o1.end_time + datetime.timedelta(days=-2),
            'end_time': o2.end_time + datetime.timedelta(days=1),
            'time_filter_type': 'within'
        })

        self.assertEqual(4, res.count())
        self.assertEqual((o1.to_dict(), o2.to_dict(), o3.to_dict(),
                          o4.to_dict()),
                         (res[0].to_dict(), res[1].to_dict(),
                          res[2].to_dict(), res[3].to_dict()))


class TestLeaseAPI(base.DBTestCase):

    def test_lease_get_by_uuid(self):
        o1 = api.offer_create(test_offer_2)
        test_lease_4['offer_uuid'] = o1.uuid
        l1 = api.lease_create(test_lease_4)
        res = api.lease_get_by_uuid(l1.uuid)
        self.assertEqual(l1.uuid, res.uuid)

    def test_lease_get_by_uuid_not_found(self):
        assert api.lease_get_by_uuid('some_uuid') is None

    def test_lease_get_by_name(self):
        o1 = api.offer_create(test_offer_1)
        o2 = api.offer_create(test_offer_2)
        o3 = api.offer_create(test_offer_3)
        o4 = api.offer_create(test_offer_4)
        test_lease_1['offer_uuid'] = o1.uuid
        test_lease_2['offer_uuid'] = o2.uuid
        test_lease_3['offer_uuid'] = o3.uuid
        test_lease_4['offer_uuid'] = o4.uuid
        l1 = api.lease_create(test_lease_1)
        l2 = api.lease_create(test_lease_2)
        l3 = api.lease_create(test_lease_3)
        api.lease_create(test_lease_4)
        res = api.lease_get_by_name('l1')
        assert len(res) == 3
        self.assertEqual(l1.uuid, res[0].uuid)
        self.assertEqual(l1.project_id, res[0].project_id)

        self.assertEqual(l2.uuid, res[1].uuid)
        self.assertEqual(l2.project_id, res[1].project_id)

        self.assertEqual(l3.uuid, res[2].uuid)
        self.assertEqual(l3.project_id, res[2].project_id)

    def test_lease_get_by_name_not_found(self):
        self.assertEqual(api.lease_get_by_name('some_name'), [])

    def test_lease_get_all(self):
        api.lease_create(test_lease_1)
        api.lease_create(test_lease_2)

        res = api.lease_get_all({})
        res_uuids = [res_lease.to_dict()['uuid'] for res_lease in res]

        self.assertEqual(2, res.count())
        self.assertIn(test_lease_1['uuid'], res_uuids)
        self.assertIn(test_lease_2['uuid'], res_uuids)

    def test_lease_get_all_filter_by_status(self):
        api.lease_create(test_lease_1)
        api.lease_create(test_lease_2)
        api.lease_create(test_lease_3)
        api.lease_create(test_lease_4)
        api.lease_create(test_lease_5)

        res = api.lease_get_all({'status': [statuses.CREATED,
                                            statuses.ACTIVE]})
        res_uuids = [res_lease.to_dict()['uuid'] for res_lease in res]

        self.assertEqual(3, res.count())
        self.assertIn(test_lease_1['uuid'], res_uuids)
        self.assertIn(test_lease_2['uuid'], res_uuids)
        self.assertIn(test_lease_3['uuid'], res_uuids)

    def test_lease_get_all_filter_by_time(self):
        api.lease_create(test_lease_1)
        api.lease_create(test_lease_2)
        api.lease_create(test_lease_3)

        start_time = test_lease_2['start_time'] + datetime.timedelta(days=1)
        end_time = test_lease_2['end_time'] + datetime.timedelta(days=-1)

        res = api.lease_get_all({'start_time': start_time,
                                 'end_time': end_time})
        res_uuids = [res_lease.to_dict()['uuid'] for res_lease in res]

        self.assertEqual(1, res.count())
        self.assertIn(test_lease_2['uuid'], res_uuids)

    def test_lease_get_all_filter_by_time_within(self):
        api.lease_create(test_lease_1)
        api.lease_create(test_lease_2)
        api.lease_create(test_lease_3)
        api.lease_create(test_lease_6)

        start_time = test_lease_1['end_time'] + datetime.timedelta(days=-1)
        end_time = test_lease_2['start_time'] + datetime.timedelta(days=1)

        res = api.lease_get_all({'start_time': start_time,
                                 'end_time': end_time,
                                 'time_filter_type': 'within'})
        res_uuids = [res_lease.to_dict()['uuid'] for res_lease in res]

        self.assertEqual(3, res.count())
        self.assertIn(test_lease_1['uuid'], res_uuids)
        self.assertIn(test_lease_2['uuid'], res_uuids)
        self.assertIn(test_lease_6['uuid'], res_uuids)

    def test_lease_get_all_filter_by_project_or_owner_id(self):
        api.lease_create(test_lease_1)
        api.lease_create(test_lease_2)
        api.lease_create(test_lease_3)
        api.lease_create(test_lease_4)
        api.lease_create(test_lease_5)

        res = api.lease_get_all({'project_or_owner_id': '0wn3r'})
        res_uuids = [res_lease.to_dict()['uuid'] for res_lease in res]

        self.assertEqual(3, res.count())
        self.assertIn(test_lease_1['uuid'], res_uuids)
        self.assertIn(test_lease_2['uuid'], res_uuids)
        self.assertIn(test_lease_5['uuid'], res_uuids)

    def test_lease_create(self):
        o1 = api.offer_create(test_offer_2)
        test_lease_4['offer_uuid'] = o1.uuid
        l1 = api.lease_create(test_lease_4)
        l2 = api.lease_get_all({}).all()
        assert len(l2) == 1
        assert l2[0].to_dict() == l1.to_dict()

    def test_lease_update(self):
        o1 = api.offer_create(test_offer_2)
        test_lease_4['offer_uuid'] = o1.uuid
        l1 = api.lease_create(test_lease_4)
        values = {'start_time': test_lease_5['start_time'],
                  'end_time': test_lease_5['end_time']}
        api.lease_update(l1.uuid, values)
        l1 = api.lease_get_by_uuid(l1.uuid)
        self.assertEqual(test_lease_5['start_time'], l1.start_time)
        self.assertEqual(test_lease_5['end_time'], l1.end_time)

    def test_lease_update_invalid_time(self):
        o1 = api.offer_create(test_offer_3)
        test_lease_4['offer_uuid'] = o1.uuid
        l1 = api.lease_create(test_lease_4)
        values = {'start_time': now + datetime.timedelta(days=101),
                  'end_time': now}
        self.assertRaises(e.InvalidTimeRange, api.lease_update,
                          l1.uuid, values)

    def test_lease_destroy(self):
        o1 = api.offer_create(test_offer_2)
        test_lease_4['offer_uuid'] = o1.uuid
        l1 = api.lease_create(test_lease_4)
        api.lease_destroy(l1.uuid)
        self.assertEqual(api.lease_get_by_uuid('lease_4'), None)

    def test_lease_destroy_not_found(self):
        self.assertEqual(api.lease_get_by_uuid('lease_4'), None)


class TestLeaseVerifyChildAvailability(base.DBTestCase):

    def setUp(self):
        super(TestLeaseVerifyChildAvailability, self).setUp()

        self.parent_lease_data = dict(
            uuid=uuidutils.generate_uuid(),
            project_id=uuidutils.generate_uuid(),
            owner_id=uuidutils.generate_uuid(),
            resource_uuid='1111',
            resource_type='dummy_node',
            purpose='test_purpose',
            start_time=now + datetime.timedelta(days=50),
            end_time=now + datetime.timedelta(days=100),
            status=statuses.ACTIVE,
        )
        self.child_lease_data = dict(
            uuid=uuidutils.generate_uuid(),
            project_id=uuidutils.generate_uuid(),
            owner_id=uuidutils.generate_uuid(),
            parent_lease_uuid=self.parent_lease_data['uuid'],
            resource_uuid='1111',
            resource_type='dummy_node',
            purpose='test_purpose',
            start_time=now + datetime.timedelta(days=60),
            end_time=now + datetime.timedelta(days=70),
            status=statuses.ACTIVE,
        )
        self.child_offer_data = dict(
            uuid=uuidutils.generate_uuid(),
            project_id=uuidutils.generate_uuid(),
            parent_lease_uuid=self.parent_lease_data['uuid'],
            resource_uuid='1111',
            resource_type='dummy_node',
            start_time=now + datetime.timedelta(days=70),
            end_time=now + datetime.timedelta(days=80),
            status=statuses.AVAILABLE,
        )

    def test_lease_verify_child_availability(self):
        parent_lease = api.lease_create(self.parent_lease_data)

        start = (self.parent_lease_data['start_time'] +
                 datetime.timedelta(days=1))
        end = self.parent_lease_data['end_time'] + datetime.timedelta(days=-1)
        api.lease_verify_child_availability(parent_lease, start, end)

        start = (self.parent_lease_data['start_time'] +
                 datetime.timedelta(days=-1))
        end = self.parent_lease_data['end_time'] + datetime.timedelta(days=-1)
        self.assertRaises(e.LeaseNoTimeAvailabilities,
                          api.lease_verify_child_availability,
                          parent_lease, start, end,)

        start = (self.parent_lease_data['start_time'] +
                 datetime.timedelta(days=1))
        end = self.parent_lease_data['end_time'] + datetime.timedelta(days=1)
        self.assertRaises(e.LeaseNoTimeAvailabilities,
                          api.lease_verify_child_availability,
                          parent_lease, start, end,)

        start = (self.parent_lease_data['start_time'] +
                 datetime.timedelta(days=-1))
        end = self.parent_lease_data['end_time'] + datetime.timedelta(days=1)
        self.assertRaises(e.LeaseNoTimeAvailabilities,
                          api.lease_verify_child_availability,
                          parent_lease, start, end,)

    def test_lease_verify_child_availability_lease_conflict(self):
        parent_lease = api.lease_create(self.parent_lease_data)
        api.lease_create(self.child_lease_data)

        start = (self.child_lease_data['start_time'] +
                 datetime.timedelta(days=-5))
        end = self.child_lease_data['start_time'] + datetime.timedelta(days=-1)
        api.lease_verify_child_availability(parent_lease, start, end)

        start = self.child_lease_data['end_time'] + datetime.timedelta(days=1)
        end = self.child_lease_data['end_time'] + datetime.timedelta(days=5)
        api.lease_verify_child_availability(parent_lease, start, end)

        start = (self.child_lease_data['start_time'] +
                 datetime.timedelta(days=1))
        end = self.child_lease_data['end_time'] + datetime.timedelta(days=5)
        self.assertRaises(e.LeaseNoTimeAvailabilities,
                          api.lease_verify_child_availability,
                          parent_lease, start, end,)

        start = (self.child_lease_data['start_time'] +
                 datetime.timedelta(days=-1))
        end = self.child_lease_data['end_time'] + datetime.timedelta(days=-1)
        self.assertRaises(e.LeaseNoTimeAvailabilities,
                          api.lease_verify_child_availability,
                          parent_lease, start, end,)

    def test_lease_verify_child_availability_offer_conflict(self):
        parent_lease = api.lease_create(self.parent_lease_data)
        api.offer_create(self.child_offer_data)

        start = (self.child_offer_data['start_time'] +
                 datetime.timedelta(days=-5))
        end = self.child_offer_data['start_time'] + datetime.timedelta(days=-1)
        api.lease_verify_child_availability(parent_lease, start, end)

        start = self.child_offer_data['end_time'] + datetime.timedelta(days=1)
        end = self.child_offer_data['end_time'] + datetime.timedelta(days=5)
        api.lease_verify_child_availability(parent_lease, start, end)

        start = (self.child_offer_data['start_time'] +
                 datetime.timedelta(days=1))
        end = self.child_offer_data['end_time'] + datetime.timedelta(days=5)
        self.assertRaises(e.LeaseNoTimeAvailabilities,
                          api.lease_verify_child_availability,
                          parent_lease, start, end,)

        start = (self.child_offer_data['start_time'] +
                 datetime.timedelta(days=-1))
        end = self.child_offer_data['end_time'] + datetime.timedelta(days=-1)
        self.assertRaises(e.LeaseNoTimeAvailabilities,
                          api.lease_verify_child_availability,
                          parent_lease, start, end,)


class TestResourceVerifyAvailabilityAPI(base.DBTestCase):

    def test_resource_verify_availability_offer_conflict(self):
        o1 = api.offer_create(test_offer_4)
        r_type = o1.resource_type
        r_uuid = o1.resource_uuid

        start = test_offer_4['end_time'] + datetime.timedelta(days=1)
        end = test_offer_4['end_time'] + datetime.timedelta(days=5)
        api.resource_verify_availability(r_type, r_uuid, start, end)

        start = test_offer_4['start_time'] + datetime.timedelta(days=1)
        end = test_offer_4['end_time'] + datetime.timedelta(days=-1)
        self.assertRaises(e.ResourceTimeConflict,
                          api.resource_verify_availability,
                          r_type, r_uuid, start, end)

        start = test_offer_4['start_time'] + datetime.timedelta(days=-1)
        end = test_offer_4['end_time'] + datetime.timedelta(days=1)
        self.assertRaises(e.ResourceTimeConflict,
                          api.resource_verify_availability,
                          r_type, r_uuid, start, end)

        start = test_offer_4['start_time'] + datetime.timedelta(days=-1)
        end = test_offer_4['start_time'] + datetime.timedelta(days=1)
        self.assertRaises(e.ResourceTimeConflict,
                          api.resource_verify_availability,
                          r_type, r_uuid, start, end)

        start = test_offer_4['end_time'] + datetime.timedelta(days=-1)
        end = test_offer_4['end_time'] + datetime.timedelta(days=1)
        self.assertRaises(e.ResourceTimeConflict,
                          api.resource_verify_availability,
                          r_type, r_uuid, start, end)

    def test_resource_verify_availability_lease_conflict(self):
        test_lease = api.lease_create(test_lease_1)
        r_type = test_lease.resource_type
        r_uuid = test_lease.resource_uuid

        start = test_lease_1['end_time'] + datetime.timedelta(days=1)
        end = test_lease_1['end_time'] + datetime.timedelta(days=5)
        api.resource_verify_availability(r_type, r_uuid, start, end)

        start = test_lease_1['start_time'] + datetime.timedelta(days=1)
        end = test_lease_1['end_time'] + datetime.timedelta(days=-1)
        self.assertRaises(e.ResourceTimeConflict,
                          api.resource_verify_availability,
                          r_type, r_uuid, start, end)

        start = test_lease_1['start_time'] + datetime.timedelta(days=-1)
        end = test_lease_1['end_time'] + datetime.timedelta(days=1)
        self.assertRaises(e.ResourceTimeConflict,
                          api.resource_verify_availability,
                          r_type, r_uuid, start, end)

        start = test_lease_1['start_time'] + datetime.timedelta(days=-1)
        end = test_lease_1['start_time'] + datetime.timedelta(days=1)
        self.assertRaises(e.ResourceTimeConflict,
                          api.resource_verify_availability,
                          r_type, r_uuid, start, end)

        start = test_lease_1['end_time'] + datetime.timedelta(days=-1)
        end = test_lease_1['end_time'] + datetime.timedelta(days=1)
        self.assertRaises(e.ResourceTimeConflict,
                          api.resource_verify_availability,
                          r_type, r_uuid, start, end)


class TestEventAPI(base.DBTestCase):

    def test_event_get_all(self):
        api.event_create(test_event_1)
        api.event_create(test_event_2)

        events = api.event_get_all({})
        event_ids = [event.to_dict()['id'] for event in events]

        self.assertEqual(2, events.count())
        self.assertIn(test_event_1['id'], event_ids)
        self.assertIn(test_event_2['id'], event_ids)

    def test_event_get_all_filter_by_last_event_time(self):
        api.event_create(test_event_1)
        api.event_create(test_event_2)
        api.event_create(test_event_3)

        events = api.event_get_all({'last_event_time':
                                    test_event_1['event_time']})
        event_ids = [event.to_dict()['id'] for event in events]

        self.assertEqual(1, events.count())
        self.assertIn(test_event_2['id'], event_ids)

    def test_event_get_all_filter_by_last_event_id(self):
        api.event_create(test_event_1)
        api.event_create(test_event_2)
        api.event_create(test_event_3)

        events = api.event_get_all({'last_event_id': 1})
        event_ids = [event.to_dict()['id'] for event in events]

        self.assertEqual(2, events.count())
        self.assertIn(test_event_2['id'], event_ids)
        self.assertIn(test_event_3['id'], event_ids)

    def test_event_get_all_filter_by_lessee_or_owner_id(self):
        api.event_create(test_event_1)
        api.event_create(test_event_2)
        api.event_create(test_event_3)

        events = api.event_get_all({'lessee_or_owner_id': '0wn3r'})
        event_ids = [event.to_dict()['id'] for event in events]

        self.assertEqual(2, events.count())
        self.assertIn(test_event_1['id'], event_ids)
        self.assertIn(test_event_2['id'], event_ids)

    def test_lease_create(self):
        event = api.event_create(test_event_1)
        events = api.event_get_all({}).all()
        assert len(events) == 1
        assert events[0].to_dict() == event.to_dict()
