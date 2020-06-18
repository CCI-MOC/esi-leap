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
from esi_leap.objects import contract
from esi_leap.tests.api import base as test_api_base


def create_test_contract(context):
    c = contract.Contract(
        start_date=datetime.datetime(2016, 7, 16, 19, 20, 30),
        end_date=datetime.datetime(2016, 8, 16, 19, 20, 30),
        offer_uuid='1234567890'
    )
    c.create(context)
    return c


class TestContractsController(test_api_base.APITestCase):

    def setUp(self):
        super(TestContractsController, self).setUp()

    def test_empty(self):
        data = self.get_json('/contracts')
        self.assertEqual([], data['contracts'])

    def test_one(self):

        c = create_test_contract(self.context)
        data = self.get_json('/contracts')
        self.assertEqual(c.uuid, data['contracts'][0]["uuid"])
