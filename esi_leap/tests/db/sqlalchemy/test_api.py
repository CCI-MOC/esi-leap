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
    name='o1',
    resource_uuid='1111',
    resource_type='dummy_node',
    start_time=now,
    end_time=now + datetime.timedelta(days=100),
    properties={'foo': 'bar'},
    status=statuses.AVAILABLE,
)

test_offer_3 = dict(
    uuid='33333',
    project_id='0wn3r_2',
    name='o1',
    resource_uuid='1111',
    resource_type='dummy_node',
    start_time=now,
    end_time=now + datetime.timedelta(days=100),
    properties={'foo': 'bar'},
    status=statuses.AVAILABLE,
)

test_offer_4 = dict(
    uuid='44444',
    project_id='0wn3r_2',
    name='o2',
    resource_uuid='1111',
    resource_type='dummy_node',
    start_time=now,
    end_time=now + datetime.timedelta(days=100),
    properties={'foo': 'bar'},
    status=statuses.AVAILABLE,
)

test_contract_1 = dict(
    uuid='11111',
    project_id='1e5533',
    name='c1',
    start_time=now + datetime.timedelta(days=10),
    end_time=now + datetime.timedelta(days=20),
    status=statuses.CREATED,
)

test_contract_2 = dict(
    uuid='22222',
    project_id='1e5533',
    name='c1',
    start_time=now + datetime.timedelta(days=20),
    end_time=now + datetime.timedelta(days=30),
    status=statuses.CREATED,
)

test_contract_3 = dict(
    uuid='33333',
    project_id='1e5533_2',
    name='c1',
    start_time=now + datetime.timedelta(days=50),
    end_time=now + datetime.timedelta(days=60),
    status=statuses.ACTIVE,
)

test_contract_4 = dict(
    uuid='44444',
    project_id='1e5533_2',
    name='c2',
    start_time=now + datetime.timedelta(days=85),
    end_time=now + datetime.timedelta(days=90),
    status=statuses.CANCELLED,
)


class TestAPI(base.DBTestCase):

    def test_offer_create(self):
        offer = api.offer_create(test_offer_1)
        o = api.offer_get_all({}).all()
        assert len(o) == 1
        assert o[0].to_dict() == offer.to_dict()

    def test_offer_verify_contract_availability(self):
        offer = api.offer_create(test_offer_1)

        test_contract_1['offer_uuid'] = offer.uuid
        test_contract_2['offer_uuid'] = offer.uuid
        test_contract_3['offer_uuid'] = offer.uuid

        api.contract_create(test_contract_1)
        api.contract_create(test_contract_2)
        api.contract_create(test_contract_3)

        start = now + datetime.timedelta(days=35)
        end = now + datetime.timedelta(days=40)
        api.offer_verify_contract_availability(offer, start, end)

        start = now + datetime.timedelta(days=5)
        end = now + datetime.timedelta(days=10)
        api.offer_verify_contract_availability(offer, start, end)

        start = now
        end = now + datetime.timedelta(days=10)
        api.offer_verify_contract_availability(offer, start, end)

        start = now + datetime.timedelta(days=90)
        end = now + datetime.timedelta(days=100)
        api.offer_verify_contract_availability(offer, start, end)

        start = now + datetime.timedelta(days=60)
        end = now + datetime.timedelta(days=100)
        api.offer_verify_contract_availability(offer, start, end)

        start = now + datetime.timedelta(days=30)
        end = now + datetime.timedelta(days=50)
        api.offer_verify_contract_availability(offer, start, end)

        start = now + datetime.timedelta(days=15)
        end = now + datetime.timedelta(days=16)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_contract_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=45)
        end = now + datetime.timedelta(days=55)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_contract_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=55)
        end = now + datetime.timedelta(days=65)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_contract_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=50)
        end = now + datetime.timedelta(days=65)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_contract_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=45)
        end = now + datetime.timedelta(days=60)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_contract_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=90)
        end = now + datetime.timedelta(days=105)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_contract_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=100)
        end = now + datetime.timedelta(days=105)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_contract_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=105)
        end = now + datetime.timedelta(days=110)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_contract_availability,
                          offer, start, end)

        start = now - datetime.timedelta(days=1)
        end = now + datetime.timedelta(days=5)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_contract_availability,
                          offer, start, end)

        start = now - datetime.timedelta(days=1)
        end = now
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_contract_availability,
                          offer, start, end)

        start = now - datetime.timedelta(days=10)
        end = now - datetime.timedelta(days=5)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_contract_availability,
                          offer, start, end)

        start = now + datetime.timedelta(days=45)
        end = now + datetime.timedelta(days=55)
        self.assertRaises(e.OfferNoTimeAvailabilities,
                          api.offer_verify_contract_availability,
                          offer, start, end)

        test_contract_4['offer_uuid'] = offer.uuid
        api.contract_create(test_contract_4)
        start = now + datetime.timedelta(days=86)
        end = now + datetime.timedelta(days=87)
        api.offer_verify_contract_availability(offer, start, end)

    def test_offer_get_by_uuid(self):

        offer = api.offer_create(test_offer_1)
        api.offer_create(test_offer_2)

        res = api.offer_get_by_uuid(offer.uuid)
        self.assertEqual(offer.uuid, res.uuid)
        self.assertEqual(offer.project_id, res.project_id)
        self.assertEqual(offer.properties, res.properties)

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

        assert api.offer_get_by_uuid('some_uuid') is None
