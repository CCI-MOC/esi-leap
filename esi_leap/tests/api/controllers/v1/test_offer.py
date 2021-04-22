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
import http.client as http_client
import mock
from oslo_utils import uuidutils
import testtools

from esi_leap.api.controllers.v1.offer import OffersController
from esi_leap.common import statuses
from esi_leap.objects import offer
from esi_leap.tests.api import base as test_api_base


def _get_offer_response(o):
    return {
        'resource_type': o.resource_type,
        'resource_uuid': o.resource_uuid,
        'name': o.name,
        'project_id': o.project_id,
        'start_time': '2016-07-16T00:00:00',
        'end_time': '2016-10-24T00:00:00',
        'status': o.status,
        'availabilities': [],
        'uuid': o.uuid
    }


class TestOffersController(test_api_base.APITestCase):

    def setUp(self):
        super(TestOffersController, self).setUp()

        start = datetime.datetime(2016, 7, 16)
        self.test_offer = offer.Offer(
            resource_type='test_node',
            resource_uuid=uuidutils.generate_uuid(),
            name="test_offer",
            uuid=uuidutils.generate_uuid(),
            status=statuses.AVAILABLE,
            start_time=start,
            end_time=start + datetime.timedelta(days=100),
            project_id=self.context.project_id,
        )
        self.test_offer_2 = offer.Offer(
            resource_type='test_node',
            resource_uuid=uuidutils.generate_uuid(),
            name="test_offer2",
            uuid=uuidutils.generate_uuid(),
            status=statuses.CANCELLED,
            start_time=start,
            end_time=start + datetime.timedelta(days=100),
            project_id=self.context.project_id,
        )

    def test_empty(self):
        data = self.get_json('/offers')
        self.assertEqual([], data['offers'])

    def test_one(self):
        self.test_offer.create(self.context)
        data = self.get_json('/offers')
        self.assertEqual(self.test_offer.uuid, data['offers'][0]["uuid"])

    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.api.controllers.v1.utils.check_resource_admin')
    @mock.patch('esi_leap.objects.offer.Offer.create')
    @mock.patch('esi_leap.api.controllers.v1.offer.' +
                'OffersController._add_offer_availabilities')
    def test_post(self, mock_aoa, mock_create, mock_cra, mock_generate_uuid):
        mock_generate_uuid.return_value = self.test_offer.uuid
        mock_create.return_value = self.test_offer
        mock_aoa.return_value = self.test_offer.to_dict()

        data = {
            "resource_type": self.test_offer.resource_type,
            "resource_uuid": self.test_offer.resource_uuid,
            "name": self.test_offer.name,
            "start_time": "2016-07-16T00:00:00",
            "end_time": "2016-10-24T00:00:00"
        }

        request = self.post_json('/offers', data)

        data['project_id'] = self.context.project_id
        data['uuid'] = self.test_offer.uuid
        data['status'] = statuses.AVAILABLE

        mock_cra.assert_called_once_with(self.context.to_policy_values(),
                                         self.test_offer.resource_type,
                                         self.test_offer.resource_uuid,
                                         self.context.project_id)
        mock_create.assert_called_once()
        mock_aoa.assert_called_once()
        self.assertEqual(data, request.json)
        self.assertEqual(http_client.CREATED, request.status_int)

    @mock.patch('esi_leap.objects.offer.Offer.get_availabilities')
    @mock.patch('esi_leap.objects.offer.Offer.get_all')
    def test_get_nofilters(self, mock_get_all, mock_get_availabilities):

        mock_get_all.return_value = [self.test_offer, self.test_offer_2]
        mock_get_availabilities.return_value = []

        expected_filters = {'status': 'available'}
        expected_resp = {'offers': [_get_offer_response(self.test_offer),
                                    _get_offer_response(self.test_offer_2)]}

        request = self.get_json('/offers')

        mock_get_all.assert_called_once_with(expected_filters, self.context)
        assert mock_get_availabilities.call_count == 2
        self.assertEqual(request, expected_resp)

    @mock.patch('esi_leap.objects.offer.Offer.get_availabilities')
    @mock.patch('esi_leap.objects.offer.Offer.get_all')
    def test_get_any_status(self, mock_get_all, mock_get_availabilities):

        mock_get_all.return_value = [self.test_offer, self.test_offer_2]
        mock_get_availabilities.return_value = []

        expected_filters = {}
        expected_resp = {'offers': [_get_offer_response(self.test_offer),
                                    _get_offer_response(self.test_offer_2)]}

        request = self.get_json('/offers/?status=any')

        mock_get_all.assert_called_once_with(expected_filters, self.context)
        assert mock_get_availabilities.call_count == 2
        self.assertEqual(request, expected_resp)

    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.objects.lease.Lease.create')
    @mock.patch('esi_leap.api.controllers.v1.utils.get_offer')
    def test_claim(self, mock_get_offer, mock_lease_create,
                   mock_generate_uuid):
        lease_uuid = '12345'
        mock_generate_uuid.return_value = lease_uuid
        mock_get_offer.return_value = self.test_offer
        data = {
            "name": "lease_claim",
            "start_time": "2016-07-16T19:20:30",
            "end_time": "2016-08-16T19:20:30"
        }

        request = self.post_json('/offers/' + self.test_offer.uuid + '/claim',
                                 data)

        data['project_id'] = self.context.project_id
        data['uuid'] = lease_uuid
        data['offer_uuid'] = self.test_offer.uuid
        data['resource_type'] = self.test_offer.resource_type
        data['resource_uuid'] = self.test_offer.resource_uuid
        data['owner_id'] = self.test_offer.project_id

        mock_get_offer.assert_called_once_with(self.test_offer.uuid,
                                               statuses.AVAILABLE)
        mock_lease_create.assert_called_once()
        self.assertEqual(data, request.json)
        self.assertEqual(http_client.CREATED, request.status_int)


class TestOffersControllerStaticMethods(testtools.TestCase):

    @mock.patch('esi_leap.objects.offer.Offer.get_availabilities')
    def test__add_offer_availabilities(self, mock_get_availabilities):
        mock_get_availabilities.return_value = []

        start = datetime.datetime(2016, 7, 16)
        o = offer.Offer(
            resource_type='test_node',
            resource_uuid='1234567890',
            name="o",
            status=statuses.AVAILABLE,
            start_time=start,
            end_time=start + datetime.timedelta(days=100),
            project_id=uuidutils.generate_uuid()
        )

        o_dict = OffersController._add_offer_availabilities(o)

        expected_offer_dict = {
            'resource_type': o.resource_type,
            'resource_uuid': o.resource_uuid,
            'name': o.name,
            'project_id': o.project_id,
            'start_time': o.start_time,
            'end_time': o.end_time,
            'status': o.status,
            'availabilities': [],
        }

        self.assertEqual(o_dict, expected_offer_dict)
