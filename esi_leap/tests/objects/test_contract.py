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


def get_test_contract():
    return {
        'id': 27,
        'uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'project_id': '01d4e6a72f5c408813e02f664cc8c83e',
        'start_date': None,
        'end_date': None,
        'status': statuses.OPEN,
        'properties': {},
        'offer_uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'created_at': None,
        'updated_at': None
    }


class TestContractObject(base.DBTestCase):

    def setUp(self):
        super(TestContractObject, self).setUp()
        self.fake_contract = get_test_contract()

    def test_get(self):
        contract_uuid = self.fake_contract['uuid']
        with mock.patch.object(self.db_api, 'contract_get',
                               autospec=True) as mock_contract_get:
            mock_contract_get.return_value = self.fake_contract

            c = contract.Contract.get(
                self.context, contract_uuid)

            mock_contract_get.assert_called_once_with(
                self.context, contract_uuid)
            self.assertEqual(self.context, c._context)

    def test_get_all(self):
        with mock.patch.object(
                self.db_api, 'contract_get_all', autospec=True
        ) as mock_contract_get_all:
            mock_contract_get_all.return_value = [
                self.fake_contract]

            contracts = contract.Contract.get_all(
                self.context, {})

            mock_contract_get_all.assert_called_once_with(
                self.context, {})
            self.assertEqual(len(contracts), 1)
            self.assertIsInstance(
                contracts[0], contract.Contract)
            self.assertEqual(self.context, contracts[0]._context)

    def test_create(self):
        c = contract.Contract(
            self.context, **self.fake_contract)
        with mock.patch.object(self.db_api, 'contract_create',
                               autospec=True) as mock_contract_create:
            mock_contract_create.return_value = get_test_contract()

            c.create(self.context)

            mock_contract_create.assert_called_once_with(
                self.context, get_test_contract())

    def test_destroy(self):
        c = contract.Contract(self.context, **self.fake_contract)
        with mock.patch.object(self.db_api, 'contract_destroy',
                               autospec=True) as mock_contract_destroy:

            c.destroy(self.context)

            mock_contract_destroy.assert_called_once_with(
                self.context, c.uuid)

    def test_save(self):
        c = contract.Contract(self.context, **self.fake_contract)
        new_status = statuses.FULFILLED
        updated_at = datetime.datetime(2006, 12, 11, 0, 0)
        with mock.patch.object(self.db_api, 'contract_update',
                               autospec=True) as mock_contract_update:
            updated_contract = get_test_contract()
            updated_contract['status'] = new_status
            updated_contract['updated_at'] = updated_at
            mock_contract_update.return_value = updated_contract

            c.status = new_status
            c.save(self.context)

            updated_values = get_test_contract()
            updated_values['status'] = new_status
            mock_contract_update.assert_called_once_with(
                self.context, c.uuid, updated_values)
            self.assertEqual(self.context, c._context)
            self.assertEqual(updated_at, c.updated_at)
