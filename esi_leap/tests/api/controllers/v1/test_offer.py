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

from esi_leap.objects import offer
from esi_leap.tests.api import base as test_api_base


def create_test_offer(context):
    o = offer.Offer(
        resource_type='test_node',
        resource_uuid='1234567890',
        start_time=datetime.datetime(2016, 7, 16, 19, 20, 30),
        end_time=datetime.datetime(2016, 8, 16, 19, 20, 30),
        project_id="111111111111"
    )
    o.create(context)
    return o


class TestListOffers(test_api_base.APITestCase):

    def setUp(self):
        super(TestListOffers, self).setUp()

    def test_empty(self):
        data = self.get_json('/offers')
        self.assertEqual([], data['offers'])

    def test_one(self):

        o = create_test_offer(self.context)
        data = self.get_json('/offers')
        self.assertEqual(o.uuid, data['offers'][0]["uuid"])
