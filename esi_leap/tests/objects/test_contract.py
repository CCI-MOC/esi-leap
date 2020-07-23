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
from esi_leap.objects import contract
from esi_leap.tests import base


start = datetime.datetime(2016, 7, 16, 19, 20, 30)


def get_test_contract_1():
    return {
        'id': 27,
        'name': 'c',
        'uuid': '534653c9-880d-4c2d-6d6d-11111111111',
        'project_id': 'le55ee',
        'start_time': start + datetime.timedelta(days=5),
        'end_time': start + datetime.timedelta(days=10),
        'status': statuses.CREATED,
        'properties': {},
        'offer_uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'created_at': None,
        'updated_at': None
    }


def get_test_contract_2():

    return {
        'id': 28,
        'name': 'c',
        'uuid': '534653c9-880d-4c2d-6d6d-22222222222',
        'project_id': 'le55ee',
        'start_time': start + datetime.timedelta(days=15),
        'end_time': start + datetime.timedelta(days=20),
        'status': statuses.CREATED,
        'properties': {},
        'offer_uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'created_at': None,
        'updated_at': None
    }


def get_test_contract_3():

    return {
        'id': 29,
        'name': 'c',
        'uuid': '534653c9-880d-4c2d-6d6d-33333333333',
        'project_id': 'le55ee_2',
        'start_time': start + datetime.timedelta(days=25),
        'end_time': start + datetime.timedelta(days=30),
        'status': statuses.CREATED,
        'properties': {},
        'offer_uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'created_at': None,
        'updated_at': None
    }


def get_test_contract_4():

    return {
        'id': 30,
        'name': 'c2',
        'uuid': '534653c9-880d-4c2d-6d6d-44444444444',
        'project_id': 'le55ee_2',
        'start_time': start + datetime.timedelta(days=35),
        'end_time': start + datetime.timedelta(days=40),
        'status': statuses.CREATED,
        'properties': {},
        'offer_uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'created_at': None,
        'updated_at': None
    }


def get_offer():

    class Offer(object):
        pass

    o = Offer()
    offer = dict(
        id=27,
        uuid='534653c9-880d-4c2d-6d6d-f4f2a09e384',
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


class TestContractObject(base.DBTestCase):

    def setUp(self):
        super(TestContractObject, self).setUp()
        self.fake_contract = get_test_contract_1()
        self.fake_contract_2 = get_test_contract_2()
        self.fake_contract_3 = get_test_contract_3()
        self.fake_contract_4 = get_test_contract_4()

    def test_get_by_uuid(self):
        contract_uuid = self.fake_contract['uuid']
        with mock.patch.object(self.db_api, 'contract_get_by_uuid',
                               autospec=True) as mock_contract_get_by_uuid:
            mock_contract_get_by_uuid.return_value = self.fake_contract

            c = contract.Contract.get_by_uuid(
                contract_uuid, self.context)

            mock_contract_get_by_uuid.assert_called_once_with(
                contract_uuid)
            self.assertEqual(self.context, c._context)

    def test_get_by_name(self):
        with mock.patch.object(self.db_api, 'contract_get_by_name',
                               autospec=True) as mock_contract_get_by_name:
            mock_contract_get_by_name.return_value = \
                [self.fake_contract, self.fake_contract_2,
                 self.fake_contract_3]

            c = contract.Contract.get_by_name(
                'c', self.context)

            mock_contract_get_by_name.assert_called_once_with('c')
            self.assertEqual(self.context, c[0]._context)

    def test_get(self):
        with mock.patch.object(self.db_api, 'contract_get_by_name',
                               autospec=True) as mock_contract_get_by_name:
            with mock.patch.object(self.db_api, 'contract_get_by_uuid',
                                   autospec=True) as mock_contract_get_by_uuid:

                mock_contract_get_by_name.return_value = \
                    [self.fake_contract, self.fake_contract_2,
                     self.fake_contract_3]
                mock_contract_get_by_uuid.return_value = None

                c = contract.Contract.get(
                    'c', self.context)

                mock_contract_get_by_uuid.assert_called_once_with('c')
                mock_contract_get_by_name.assert_called_once_with('c')
                assert len(c) == 3

        with mock.patch.object(self.db_api, 'contract_get_by_name',
                               autospec=True) as mock_contract_get_by_name:
            with mock.patch.object(self.db_api, 'contract_get_by_uuid',
                                   autospec=True) as mock_contract_get_by_uuid:

                mock_contract_get_by_uuid.return_value = self.fake_contract
                c = contract.Contract.get(
                    self.fake_contract['uuid'], self.context)

                mock_contract_get_by_uuid.assert_called_once_with(
                    self.fake_contract['uuid']
                )
                assert not mock_contract_get_by_name.called
                assert len(c) == 1

    def test_get_all(self):
        with mock.patch.object(
                self.db_api, 'contract_get_all', autospec=True
        ) as mock_contract_get_all:
            mock_contract_get_all.return_value = \
                [self.fake_contract, self.fake_contract_2,
                 self.fake_contract_3, self.fake_contract_4]

            contracts = contract.Contract.get_all(
                self.context, {})

            mock_contract_get_all.assert_called_once_with({})
            self.assertEqual(len(contracts), 4)
            self.assertIsInstance(
                contracts[0], contract.Contract)
            self.assertEqual(self.context, contracts[0]._context)

    def test_create(self):
        c = contract.Contract(
            self.context, **self.fake_contract)
        with mock.patch.object(self.db_api, 'contract_create',
                               autospec=True) as mock_contract_create:
            with mock.patch.object(self.db_api, 'offer_get_by_uuid',
                                   autospec=True) as mock_offer_get_by_uuid:
                with mock.patch(
                        'esi_leap.objects.contract.uuidutils.generate_uuid')\
                        as mock_uuid:
                    mock_offer_get_by_uuid.return_value = get_offer()
                    mock_contract_create.return_value = get_test_contract_1()
                    mock_uuid.return_value = '534653c9-880d-4c2d-6d6d-' \
                                             '11111111111'

                    c.create()

                    mock_contract_create.assert_called_once_with(
                        get_test_contract_1())

    def test_destroy(self):
        c = contract.Contract(self.context, **self.fake_contract)
        with mock.patch.object(self.db_api, 'contract_destroy',
                               autospec=True) as mock_contract_cancel:

            c.destroy()

            mock_contract_cancel.assert_called_once_with(
                c.uuid)

    def test_save(self):
        c = contract.Contract(self.context, **self.fake_contract)
        new_status = statuses.ACTIVE
        updated_at = datetime.datetime(2006, 12, 11, 0, 0)
        with mock.patch.object(self.db_api, 'contract_update',
                               autospec=True) as mock_contract_update:
            updated_contract = get_test_contract_1()
            updated_contract['status'] = new_status
            updated_contract['updated_at'] = updated_at
            mock_contract_update.return_value = updated_contract

            c.status = new_status
            c.save(self.context)

            updated_values = get_test_contract_1()
            updated_values['status'] = new_status
            mock_contract_update.assert_called_once_with(
                c.uuid, updated_values)
            self.assertEqual(self.context, c._context)
            self.assertEqual(updated_at, c.updated_at)
