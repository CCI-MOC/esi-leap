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
from oslo_context import context as ctx
from oslo_utils import uuidutils
import testtools

from esi_leap.api.controllers.v1.offer import OffersController
from esi_leap.common import statuses
from esi_leap.objects import offer
from esi_leap.resource_objects.test_node import TestNode
from esi_leap.tests.api import base as test_api_base


owner_ctx = ctx.RequestContext(project_id='ownerid',
                               roles=['owner'],)

owner_ctx_2 = ctx.RequestContext(project_id='ownerid2',
                                 roles=['owner'],
                                 is_admin_project=False)

admin_ctx = ctx.RequestContext(project_id='adminid',
                               roles=['admin'])

lessee_ctx = ctx.RequestContext(project_id='lesseeid',
                                roles=['lessee'])

start = datetime.datetime(2016, 7, 16)
start_iso = '2016-07-16T00:00:00'

end = start + datetime.timedelta(days=100)
end_iso = '2016-10-24T00:00:00'

test_node_1 = TestNode('aaa', owner_ctx.project_id)
test_node_2 = TestNode('bbb', owner_ctx_2.project_id)

o_uuid = uuidutils.generate_uuid()


def create_test_offer(context):
    o = offer.Offer(
        resource_type='test_node',
        resource_uuid='1234567890',
        uuid=o_uuid,
        start_time=datetime.datetime(2016, 7, 16, 19, 20, 30),
        end_time=datetime.datetime(2016, 8, 16, 19, 20, 30),
        project_id="111111111111"
    )
    o.create(context)
    return o


def get_offer_response(o):
    return {
        'resource_type': o.resource_type,
        'resource_uuid': o.resource_uuid,
        'name': o.name,
        'project_id': o.project_id,
        'start_time': start_iso,
        'end_time': end_iso,
        'status': o.status,
        'availabilities': [],
        'uuid': o.uuid
    }


create_test_offer_data = {
    "resource_type": "test_node",
    "resource_uuid": 'aaa',
    "name": "o",
    "start_time": str(start),
    "end_time": str(end),
}

test_offer = offer.Offer(
    resource_type='test_node',
    resource_uuid=test_node_1._uuid,
    name="o",
    uuid=o_uuid,
    status=statuses.AVAILABLE,
    start_time=start,
    end_time=end,
    project_id=owner_ctx.project_id
)

test_offer_2 = offer.Offer(
    resource_type='test_node',
    resource_uuid=test_node_1._uuid,
    start_time=start,
    status=statuses.CANCELLED,
    name="o",
    uuid=uuidutils.generate_uuid(),
    end_time=end,
    project_id=owner_ctx.project_id
)


test_offer_3 = offer.Offer(
    resource_type='test_node',
    resource_uuid=test_node_2._uuid,
    name="o",
    uuid=uuidutils.generate_uuid(),
    status=statuses.AVAILABLE,
    start_time=start,
    end_time=end,
    project_id=owner_ctx_2.project_id
)


test_offer_4 = offer.Offer(
    resource_type='test_node',
    resource_uuid=test_node_2._uuid,
    name="o2",
    uuid=uuidutils.generate_uuid(),
    status=statuses.AVAILABLE,
    start_time=start,
    end_time=end,
    project_id=owner_ctx_2.project_id
)


class TestListOffers(test_api_base.APITestCase):

    def setUp(self):

        super(TestListOffers, self).setUp()
        self.test_offer = offer.Offer(
            resource_type='test_node',
            resource_uuid='1234567890',
            uuid=o_uuid,
            start_time=start,
            end_time=end,
            project_id=owner_ctx.project_id
        )

    def test_empty(self):
        data = self.get_json('/offers')
        self.assertEqual([], data['offers'])

    def test_one(self):

        self.test_offer.create(self.context)
        data = self.get_json('/offers')
        self.assertEqual(self.test_offer.uuid, data['offers'][0]["uuid"])

    @mock.patch('esi_leap.api.controllers.v1.offer.uuidutils.generate_uuid')
    @mock.patch('esi_leap.objects.offer.Offer.create')
    @mock.patch('esi_leap.api.controllers.v1.offer.utils.'
                'verify_resource_permission')
    @mock.patch('esi_leap.api.controllers.v1.offer.' +
                'OffersController._add_offer_availabilities')
    def test_post(self, mock_aoa, mock_vrp, mock_create, mock_generate_uuid):

        mock_generate_uuid.return_value = o_uuid
        mock_create.return_value = self.test_offer
        data = create_test_offer_data
        request = self.post_json('/offers', data)
        data['project_id'] = owner_ctx.project_id
        self.assertEqual(1, mock_create.call_count)
        self.assertEqual(request.json, {})
        # FIXME: post returns incorrect status code
        # self.assertEqual(http_client.CREATED, request.status_int)


class TestOffersControllerOwner(test_api_base.APITestCase):

    def setUp(self):
        self.context = owner_ctx
        super(TestOffersControllerOwner, self).setUp()

    @mock.patch('esi_leap.api.controllers.v1.offer.offer.Offer.'
                'get_availabilities')
    @mock.patch('esi_leap.api.controllers.v1.offer.offer.Offer.get_all')
    def test_get_nofilters(self, mock_get_all, mock_get_availabilities):

        mock_get_all.return_value = [test_offer, test_offer_2,
                                     test_offer_3, test_offer_4]
        mock_get_availabilities.return_value = []

        expected_filters = {'status': 'available'}
        expected_resp = {'offers': [get_offer_response(test_offer),
                                    get_offer_response(test_offer_2),
                                    get_offer_response(test_offer_3),
                                    get_offer_response(test_offer_4)]}

        request = self.get_json('/offers')

        mock_get_all.assert_called_once_with(expected_filters, self.context)
        assert mock_get_availabilities.call_count == 4
        self.assertEqual(request, expected_resp)

    @mock.patch('esi_leap.api.controllers.v1.offer.offer.Offer.'
                'get_availabilities')
    @mock.patch('esi_leap.api.controllers.v1.offer.offer.Offer.get_all')
    def test_get_any_status(self, mock_get_all, mock_get_availabilities):

        mock_get_all.return_value = [test_offer, test_offer_2,
                                     test_offer_3, test_offer_4]
        mock_get_availabilities.return_value = []

        expected_filters = {'status': 'available'}
        expected_resp = {'offers': [get_offer_response(test_offer),
                                    get_offer_response(test_offer_2),
                                    get_offer_response(test_offer_3),
                                    get_offer_response(test_offer_4)]}

        request = self.get_json('/offers')

        mock_get_all.assert_called_once_with(expected_filters, self.context)
        assert mock_get_availabilities.call_count == 4
        self.assertEqual(request, expected_resp)


class TestOffersControllerStaticMethods(testtools.TestCase):

    @mock.patch('esi_leap.api.controllers.v1.offer.offer.Offer.'
                'get_availabilities')
    def test__add_offer_availabilities(self, mock_get_availabilities):
        mock_get_availabilities.return_value = []

        o = offer.Offer(
            resource_type='test_node',
            resource_uuid='1234567890',
            name="o",
            status=statuses.AVAILABLE,
            start_time=start,
            end_time=end,
            project_id=owner_ctx.project_id
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
