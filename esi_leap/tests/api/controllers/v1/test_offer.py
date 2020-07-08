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
import mock


def create_test_offer_data():

    return {
        "resource_type": "test_node",
        "resource_uuid": "1234567890",
        "start_time": "2016-07-16T19:20:30",
        "end_time": "2016-08-16T19:20:30",
        "project_id": "111111111111"
    }


class TestListOffers(test_api_base.APITestCase):

    def setUp(self):
        super(TestListOffers, self).setUp()
        self.test_offer = offer.Offer(
            resource_type='test_node',
            resource_uuid='1234567890',
            start_time=datetime.datetime(2016, 7, 16, 19, 20, 30),
            end_time=datetime.datetime(2016, 8, 16, 19, 20, 30),
            project_id="111111111111"
        )

    def test_empty(self):
        data = self.get_json('/offers')
        self.assertEqual([], data['offers'])

    def test_one(self):

        self.test_offer.create(self.context)
        data = self.get_json('/offers')
        self.assertEqual(self.test_offer.uuid, data['offers'][0]["uuid"])

    @mock.patch('esi_leap.objects.offer.Offer.create')
    @mock.patch('esi_leap.api.controllers.v1.offer.' +
                'OffersController._verify_resource_permission')
    @mock.patch('esi_leap.api.controllers.v1.offer.' +
                'OffersController._add_offer_availabilities')
    def test_post(self, mock_aoa, mock_vrp, mock_create):

        mock_create.return_value = self.test_offer
        data = create_test_offer_data()
        request = self.post_json('/offers', data)
        self.assertEqual(1, mock_create.call_count)
        self.assertEqual(request.json, {})
        # FIXME: post returns incorrect status code
        # self.assertEqual(http_client.CREATED, request.status_int)
