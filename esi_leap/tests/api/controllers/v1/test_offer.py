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

from esi_leap.common import exception
from esi_leap.common import statuses
from esi_leap.objects import offer
from esi_leap.resource_objects.ironic_node import IronicNode
from esi_leap.resource_objects.test_node import TestNode
from esi_leap.tests.api import base as test_api_base


def _get_offer_response(o, use_datetime=False):
    if use_datetime:
        start = datetime.datetime(2016, 7, 16)
        end = datetime.datetime(2016, 10, 24)
    else:
        start = '2016-07-16T00:00:00'
        end = '2016-10-24T00:00:00'
    if o.resource_type in ['test_node', 'dummy_node']:
        resource_class = 'fake'
    elif o.resource_type == 'ironic_node':
        resource_class = 'baremetal'

    return {
        'resource_type': o.resource_type,
        'resource_uuid': o.resource_uuid,
        'resource_class': resource_class,
        'name': o.name,
        'project_id': o.project_id,
        'start_time': start,
        'end_time': end,
        'status': o.status,
        'availabilities': [],
        'uuid': o.uuid,
        'parent_lease_uuid': None
    }


class TestOffersController(test_api_base.APITestCase):

    def setUp(self):
        super(TestOffersController, self).setUp()

        start = datetime.datetime(2016, 7, 16)
        self.test_offer = offer.Offer(
            resource_type='test_node',
            resource_uuid=uuidutils.generate_uuid(),
            name='test_offer',
            uuid=uuidutils.generate_uuid(),
            status=statuses.AVAILABLE,
            start_time=start,
            end_time=start + datetime.timedelta(days=100),
            project_id=self.context.project_id,
            parent_lease_uuid=None
        )
        self.test_offer_drt = offer.Offer(
            resource_type='ironic_node',
            resource_uuid=uuidutils.generate_uuid(),
            name='test_offer',
            uuid=uuidutils.generate_uuid(),
            status=statuses.AVAILABLE,
            start_time=start,
            end_time=start + datetime.timedelta(days=100),
            project_id=self.context.project_id,
            parent_lease_uuid=None
        )
        self.test_offer_lessee = offer.Offer(
            resource_type='test_node',
            resource_uuid=uuidutils.generate_uuid(),
            name='test_offer',
            uuid=uuidutils.generate_uuid(),
            lessee_id='lessee-uuid',
            status=statuses.AVAILABLE,
            start_time=start,
            end_time=start + datetime.timedelta(days=100),
            project_id=self.context.project_id,
            parent_lease_uuid=None
        )
        self.test_offer_2 = offer.Offer(
            resource_type='test_node',
            resource_uuid=uuidutils.generate_uuid(),
            name='test_offer2',
            uuid=uuidutils.generate_uuid(),
            status=statuses.DELETED,
            start_time=start,
            end_time=start + datetime.timedelta(days=100),
            project_id=self.context.project_id,
            parent_lease_uuid=None
        )
        self.test_offer_with_parent = offer.Offer(
            resource_type='test_node',
            resource_uuid=uuidutils.generate_uuid(),
            name='test_offer',
            uuid=uuidutils.generate_uuid(),
            status=statuses.AVAILABLE,
            start_time=start,
            end_time=start + datetime.timedelta(days=100),
            project_id=self.context.project_id,
            parent_lease_uuid='parent-lease-uuid'
        )

    def test_empty(self):
        data = self.get_json('/offers')
        self.assertEqual([], data['offers'])

    @mock.patch('esi_leap.api.controllers.v1.offer.get_resource_object')
    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.api.controllers.v1.utils.check_resource_admin')
    @mock.patch('esi_leap.objects.offer.Offer.create')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'offer_get_dict_with_added_info')
    def test_post(self, mock_ogdwai, mock_create, mock_cra,
                  mock_generate_uuid, mock_gro):
        resource = TestNode(self.test_offer.resource_uuid)
        mock_gro.return_value = resource
        mock_generate_uuid.return_value = self.test_offer.uuid
        mock_create.return_value = self.test_offer
        mock_ogdwai.return_value = self.test_offer.to_dict()

        data = {
            'resource_type': self.test_offer.resource_type,
            'resource_uuid': self.test_offer.resource_uuid,
            'name': self.test_offer.name,
            'start_time': '2016-07-16T00:00:00',
            'end_time': '2016-10-24T00:00:00'
        }

        request = self.post_json('/offers', data)

        data['project_id'] = self.context.project_id
        data['uuid'] = self.test_offer.uuid
        data['status'] = statuses.AVAILABLE
        data['parent_lease_uuid'] = None

        mock_gro.assert_called_once_with(self.test_offer.resource_type,
                                         self.test_offer.resource_uuid)
        mock_cra.assert_called_once_with(
            self.context.to_policy_values(),
            resource,
            self.context.project_id)
        mock_create.assert_called_once()
        mock_ogdwai.assert_called_once()
        self.assertEqual(data, request.json)
        self.assertEqual(http_client.CREATED, request.status_int)

    @mock.patch('esi_leap.api.controllers.v1.offer.get_resource_object')
    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.api.controllers.v1.utils.check_resource_admin')
    @mock.patch('esi_leap.objects.offer.Offer.create')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'offer_get_dict_with_added_info')
    def test_post_default_resource_type(self, mock_ogdwai, mock_create,
                                        mock_cra, mock_generate_uuid,
                                        mock_gro):
        resource = IronicNode(self.test_offer_drt.resource_uuid)
        mock_gro.return_value = resource
        mock_generate_uuid.return_value = self.test_offer_drt.uuid
        mock_ogdwai.return_value = self.test_offer_drt.to_dict()

        data = {
            'resource_uuid': self.test_offer_drt.resource_uuid,
            'name': self.test_offer_drt.name,
            'start_time': '2016-07-16T00:00:00',
            'end_time': '2016-10-24T00:00:00'
        }

        request = self.post_json('/offers', data)

        data['project_id'] = self.context.project_id
        data['uuid'] = self.test_offer_drt.uuid
        data['status'] = statuses.AVAILABLE
        data['resource_type'] = 'ironic_node'
        data['parent_lease_uuid'] = None

        mock_gro.assert_called_once_with(self.test_offer_drt.resource_type,
                                         self.test_offer_drt.resource_uuid)
        mock_cra.assert_called_once_with(
            self.context.to_policy_values(),
            resource,
            self.context.project_id)
        mock_create.assert_called_once()
        mock_ogdwai.assert_called_once()
        self.assertEqual(data, request.json)
        self.assertEqual(http_client.CREATED, request.status_int)

    @mock.patch('esi_leap.api.controllers.v1.offer.get_resource_object')
    @mock.patch('esi_leap.common.keystone.get_project_uuid_from_ident')
    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.api.controllers.v1.utils.check_resource_admin')
    @mock.patch('esi_leap.objects.offer.Offer.create')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'offer_get_dict_with_added_info')
    def test_post_lessee(self, mock_ogdwai, mock_create, mock_cra,
                         mock_generate_uuid, mock_gpufi, mock_gro):
        resource = TestNode(self.test_offer_lessee.resource_uuid)
        mock_gro.return_value = resource
        mock_gpufi.return_value = 'lessee_uuid'
        mock_generate_uuid.return_value = self.test_offer_lessee.uuid
        mock_create.return_value = self.test_offer_lessee
        mock_ogdwai.return_value = self.test_offer_lessee.to_dict()

        data = {
            'resource_type': self.test_offer_lessee.resource_type,
            'resource_uuid': self.test_offer_lessee.resource_uuid,
            'name': self.test_offer_lessee.name,
            'start_time': '2016-07-16T00:00:00',
            'end_time': '2016-10-24T00:00:00',
            'lessee_id': 'lessee-uuid'
        }

        request = self.post_json('/offers', data)

        data['project_id'] = self.context.project_id
        data['uuid'] = self.test_offer_lessee.uuid
        data['status'] = statuses.AVAILABLE
        data['parent_lease_uuid'] = None

        mock_gro.assert_called_once_with(self.test_offer_lessee.resource_type,
                                         self.test_offer_lessee.resource_uuid)
        mock_gpufi.assert_called_once_with('lessee-uuid')
        mock_cra.assert_called_once_with(
            self.context.to_policy_values(),
            resource,
            self.context.project_id)
        mock_create.assert_called_once()
        mock_ogdwai.assert_called_once()
        self.assertEqual(data, request.json)
        self.assertEqual(http_client.CREATED, request.status_int)

    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'check_resource_lease_admin')
    @mock.patch('esi_leap.api.controllers.v1.offer.get_resource_object')
    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.api.controllers.v1.utils.check_resource_admin')
    @mock.patch('esi_leap.objects.offer.Offer.create')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'offer_get_dict_with_added_info')
    def test_post_non_admin_parent_lease(self, mock_ogdwai, mock_create,
                                         mock_cra, mock_generate_uuid,
                                         mock_gro, mock_crla):
        resource = TestNode(self.test_offer_with_parent.resource_uuid)
        mock_gro.return_value = resource
        mock_generate_uuid.return_value = self.test_offer_with_parent.uuid
        mock_create.return_value = self.test_offer_with_parent
        mock_ogdwai.return_value = self.test_offer_with_parent.to_dict()
        mock_cra.side_effect = exception.HTTPResourceForbidden(
            resource_type='test_node',
            resource=self.test_offer_with_parent.resource_uuid)
        mock_crla.return_value = self.test_offer_with_parent.parent_lease_uuid

        data = {
            'resource_type': self.test_offer_with_parent.resource_type,
            'resource_uuid': self.test_offer_with_parent.resource_uuid,
            'name': self.test_offer_with_parent.name,
            'start_time': '2016-07-16T00:00:00',
            'end_time': '2016-10-24T00:00:00'
        }

        request = self.post_json('/offers', data)

        data['project_id'] = self.context.project_id
        data['uuid'] = self.test_offer_with_parent.uuid
        data['status'] = statuses.AVAILABLE
        data['parent_lease_uuid'] = (
            self.test_offer_with_parent.parent_lease_uuid)

        mock_gro.assert_called_once_with(
            self.test_offer_with_parent.resource_type,
            self.test_offer_with_parent.resource_uuid)
        mock_cra.assert_called_once_with(
            self.context.to_policy_values(),
            resource,
            self.context.project_id)
        mock_crla.assert_called_once_with(
            self.context.to_policy_values(),
            resource,
            self.context.project_id,
            datetime.datetime(2016, 7, 16, 0, 0, 0),
            datetime.datetime(2016, 10, 24, 0, 0, 0))
        mock_create.assert_called_once()
        mock_ogdwai.assert_called_once()
        self.assertEqual(data, request.json)
        self.assertEqual(http_client.CREATED, request.status_int)

    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'check_resource_lease_admin')
    @mock.patch('esi_leap.api.controllers.v1.offer.get_resource_object')
    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.api.controllers.v1.utils.check_resource_admin')
    @mock.patch('esi_leap.objects.offer.Offer.create')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'offer_get_dict_with_added_info')
    def test_post_non_admin_no_parent_lease(self, mock_ogdwai, mock_create,
                                            mock_cra, mock_generate_uuid,
                                            mock_gro, mock_crla):
        resource = TestNode(self.test_offer_with_parent.resource_uuid)
        mock_gro.return_value = resource
        mock_generate_uuid.return_value = self.test_offer_with_parent.uuid
        mock_create.return_value = self.test_offer_with_parent
        mock_ogdwai.return_value = self.test_offer_with_parent.to_dict()
        mock_cra.side_effect = exception.HTTPResourceForbidden(
            resource_type='test_node',
            resource=self.test_offer_with_parent.resource_uuid)
        mock_crla.return_value = None

        data = {
            'resource_type': self.test_offer_with_parent.resource_type,
            'resource_uuid': self.test_offer_with_parent.resource_uuid,
            'name': self.test_offer_with_parent.name,
            'start_time': '2016-07-16T00:00:00',
            'end_time': '2016-10-24T00:00:00'
        }

        request = self.post_json('/offers', data, expect_errors=True)

        mock_gro.assert_called_once_with(
            self.test_offer_with_parent.resource_type,
            self.test_offer_with_parent.resource_uuid)
        mock_cra.assert_called_once_with(
            self.context.to_policy_values(),
            resource,
            self.context.project_id)
        mock_crla.assert_called_once_with(
            self.context.to_policy_values(),
            resource,
            self.context.project_id,
            datetime.datetime(2016, 7, 16, 0, 0, 0),
            datetime.datetime(2016, 10, 24, 0, 0, 0))
        mock_create.assert_not_called()
        mock_ogdwai.assert_not_called()
        self.assertEqual(http_client.FORBIDDEN, request.status_int)

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'offer_get_dict_with_added_info')
    @mock.patch('esi_leap.objects.offer.Offer.get_all')
    def test_get_nofilters(self, mock_get_all, mock_ogdwai, mock_gpl,
                           mock_gnl):
        mock_get_all.return_value = [self.test_offer, self.test_offer_2]
        mock_ogdwai.side_effect = [
            _get_offer_response(self.test_offer, use_datetime=True),
            _get_offer_response(self.test_offer_2, use_datetime=True)]
        mock_gpl.return_value = []
        mock_gnl.return_value = []

        expected_filters = {'status': statuses.OFFER_CAN_DELETE}
        expected_resp = {'offers': [_get_offer_response(self.test_offer),
                                    _get_offer_response(self.test_offer_2)]}

        request = self.get_json('/offers')

        mock_get_all.assert_called_once_with(expected_filters, self.context)
        mock_gpl.assert_called_once()
        mock_gnl.assert_called_once()
        assert mock_ogdwai.call_count == 2
        self.assertEqual(request, expected_resp)

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'offer_get_dict_with_added_info')
    @mock.patch('esi_leap.objects.offer.Offer.get_all')
    def test_get_any_status(self, mock_get_all, mock_ogdwai, mock_gpl,
                            mock_gnl):
        mock_get_all.return_value = [self.test_offer, self.test_offer_2]
        mock_ogdwai.side_effect = [
            _get_offer_response(self.test_offer, use_datetime=True),
            _get_offer_response(self.test_offer_2, use_datetime=True)]
        mock_gpl.return_value = []
        mock_gnl.return_value = []

        expected_filters = {}
        expected_resp = {'offers': [_get_offer_response(self.test_offer),
                                    _get_offer_response(self.test_offer_2)]}

        request = self.get_json('/offers/?status=any')

        mock_get_all.assert_called_once_with(expected_filters, self.context)
        mock_gpl.assert_called_once()
        mock_gnl.assert_called_once()
        assert mock_ogdwai.call_count == 2
        self.assertEqual(request, expected_resp)

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'offer_get_dict_with_added_info')
    @mock.patch('esi_leap.objects.offer.Offer.get_all')
    def test_get_status_filter(self, mock_get_all, mock_ogdwai,
                               mock_gpl, mock_gnl):
        mock_get_all.return_value = [self.test_offer, self.test_offer_2]
        mock_ogdwai.side_effect = [
            _get_offer_response(self.test_offer, use_datetime=True),
            _get_offer_response(self.test_offer_2, use_datetime=True)]
        mock_gpl.return_value = []
        mock_gnl.return_value = []

        expected_filters = {'status': [statuses.AVAILABLE]}
        expected_resp = {'offers': [_get_offer_response(self.test_offer),
                                    _get_offer_response(self.test_offer_2)]}

        request = self.get_json(
            '/offers/?status=available')

        mock_get_all.assert_called_once_with(expected_filters, self.context)
        mock_gpl.assert_called_once()
        mock_gnl.assert_called_once()
        assert mock_ogdwai.call_count == 2
        self.assertEqual(request, expected_resp)

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    @mock.patch('esi_leap.common.keystone.get_project_uuid_from_ident')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'offer_get_dict_with_added_info')
    @mock.patch('esi_leap.objects.offer.Offer.get_all')
    def test_get_project_filter(self, mock_get_all, mock_ogdwai,
                                mock_gpufi, mock_gpl, mock_gnl):
        mock_get_all.return_value = [self.test_offer, self.test_offer_2]
        mock_ogdwai.side_effect = [
            _get_offer_response(self.test_offer, use_datetime=True),
            _get_offer_response(self.test_offer_2, use_datetime=True)]
        mock_gpufi.return_value = self.context.project_id
        mock_gpl.return_value = []
        mock_gnl.return_value = []

        expected_filters = {'project_id': self.context.project_id,
                            'status': statuses.OFFER_CAN_DELETE}
        expected_resp = {'offers': [_get_offer_response(self.test_offer),
                                    _get_offer_response(self.test_offer_2)]}

        request = self.get_json(
            '/offers/?project_id=' + self.context.project_id)

        mock_gpufi.assert_called_once_with(self.context.project_id)
        mock_get_all.assert_called_once_with(expected_filters, self.context)
        mock_gpl.assert_called_once()
        mock_gnl.assert_called_once()
        assert mock_ogdwai.call_count == 2
        self.assertEqual(request, expected_resp)

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    @mock.patch('esi_leap.api.controllers.v1.offer.get_resource_object')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'offer_get_dict_with_added_info')
    @mock.patch('esi_leap.objects.offer.Offer.get_all')
    def test_get_resource_filter(self, mock_get_all, mock_ogdwai, mock_gro,
                                 mock_gpl, mock_gnl):
        mock_get_all.return_value = [self.test_offer, self.test_offer_2]
        mock_ogdwai.side_effect = [
            _get_offer_response(self.test_offer, use_datetime=True),
            _get_offer_response(self.test_offer_2, use_datetime=True)]
        mock_gro.return_value = TestNode('54321')
        mock_gpl.return_value = []
        mock_gnl.return_value = []

        expected_filters = {'status': statuses.OFFER_CAN_DELETE,
                            'resource_uuid': '54321',
                            'resource_type': 'test_node'}
        expected_resp = {'offers': [_get_offer_response(self.test_offer),
                                    _get_offer_response(self.test_offer_2)]}

        request = self.get_json('/offers/?resource_uuid=54321&'
                                'resource_type=test_node')

        mock_gro.assert_called_once_with('test_node', '54321')
        mock_get_all.assert_called_once_with(expected_filters, self.context)
        mock_gpl.assert_called_once()
        mock_gnl.assert_called_once()
        assert mock_ogdwai.call_count == 2
        self.assertEqual(request, expected_resp)

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'offer_get_dict_with_added_info')
    @mock.patch('esi_leap.objects.offer.Offer.get_all')
    def test_get_resource_class_filter(self, mock_get_all, mock_ogdwai,
                                       mock_gpl, mock_gnl):
        mock_get_all.return_value = [self.test_offer,
                                     self.test_offer_2, self.test_offer_drt]
        mock_ogdwai.side_effect = [
            _get_offer_response(self.test_offer, use_datetime=True),
            _get_offer_response(self.test_offer_2, use_datetime=True),
            _get_offer_response(self.test_offer_drt, use_datetime=True)]
        mock_gpl.return_value = []
        mock_gnl.return_value = []
        expected_filters = {'status': statuses.OFFER_CAN_DELETE}
        expected_resp = {'offers': [_get_offer_response(self.test_offer),
                                    _get_offer_response(self.test_offer_2)]}
        request = self.get_json('/offers/?resource_class=fake')

        mock_get_all.assert_called_once_with(expected_filters, self.context)
        mock_gpl.assert_called_once()
        mock_gnl.assert_called_once()
        assert mock_ogdwai.call_count == 3
        self.assertEqual(request, expected_resp)

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    @mock.patch('esi_leap.api.controllers.v1.offer.get_resource_object')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'offer_get_dict_with_added_info')
    @mock.patch('esi_leap.objects.offer.Offer.get_all')
    def test_get_resource_filter_default_resource_type(self, mock_get_all,
                                                       mock_ogdwai,
                                                       mock_gro,
                                                       mock_gpl,
                                                       mock_gnl):
        fake_uuid = uuidutils.generate_uuid()
        mock_get_all.return_value = [self.test_offer, self.test_offer_2]
        mock_ogdwai.side_effect = [
            _get_offer_response(self.test_offer, use_datetime=True),
            _get_offer_response(self.test_offer_2, use_datetime=True)]
        mock_gro.return_value = IronicNode(fake_uuid)
        mock_gpl.return_value = []
        mock_gnl.return_value = []

        expected_filters = {'status': statuses.OFFER_CAN_DELETE,
                            'resource_uuid': fake_uuid,
                            'resource_type': 'ironic_node'}
        expected_resp = {'offers': [_get_offer_response(self.test_offer),
                                    _get_offer_response(self.test_offer_2)]}

        request = self.get_json('/offers/?resource_uuid=%s' % fake_uuid)
        mock_gro.assert_called_once_with('ironic_node', fake_uuid)
        mock_get_all.assert_called_once_with(expected_filters, self.context)
        mock_gpl.assert_called_once()
        mock_gnl.assert_called_once()
        assert mock_ogdwai.call_count == 2
        self.assertEqual(request, expected_resp)

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'offer_get_dict_with_added_info')
    @mock.patch('esi_leap.objects.offer.Offer.get_all')
    @mock.patch('esi_leap.api.controllers.v1.utils.policy_authorize')
    def test_get_lessee_filter(self, mock_authorize, mock_get_all,
                               mock_ogdwai, mock_gpl, mock_gnl):
        mock_get_all.return_value = [self.test_offer, self.test_offer_2]
        mock_ogdwai.side_effect = [
            _get_offer_response(self.test_offer, use_datetime=True),
            _get_offer_response(self.test_offer_2, use_datetime=True)]
        mock_authorize.side_effect = [
            None,
            exception.HTTPForbidden(rule='esi_leap:offer:get')
        ]
        mock_gpl.return_value = []
        mock_gnl.return_value = []

        expected_filters = {'status': statuses.OFFER_CAN_DELETE,
                            'lessee_id': self.context.project_id}
        expected_resp = {'offers': [_get_offer_response(self.test_offer),
                                    _get_offer_response(self.test_offer_2)]}

        request = self.get_json('/offers')

        mock_get_all.assert_called_once_with(expected_filters, self.context)
        mock_gpl.assert_called_once()
        mock_gnl.assert_called_once()
        assert mock_ogdwai.call_count == 2
        self.assertEqual(request, expected_resp)

    @mock.patch('esi_leap.api.controllers.v1.utils.check_offer_lessee')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'check_offer_policy_and_retrieve')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'offer_get_dict_with_added_info')
    def test_get_one(self, mock_ogdwai, mock_copar, mock_col):
        mock_copar.return_value = self.test_offer
        mock_ogdwai.return_value = self.test_offer.to_dict()

        self.get_json('/offers/' + self.test_offer.uuid)

        mock_copar.assert_called_once_with(self.context,
                                           'esi_leap:offer:get',
                                           self.test_offer.uuid)
        mock_col.assert_called_once_with(self.context.to_policy_values(),
                                         self.test_offer)
        mock_ogdwai.assert_called_once_with(self.test_offer)

    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.objects.lease.Lease.create')
    @mock.patch('esi_leap.api.controllers.v1.utils.check_offer_lessee')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'check_offer_policy_and_retrieve')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'lease_get_dict_with_added_info')
    def test_claim(self, mock_lgdwai, mock_copar, mock_col, mock_lease_create,
                   mock_generate_uuid):
        lease_uuid = '12345'
        mock_generate_uuid.return_value = lease_uuid
        mock_copar.return_value = self.test_offer
        data = {
            'name': 'lease_claim',
            'start_time': '2016-07-16T19:20:30',
            'end_time': '2016-08-16T19:20:30'
        }

        request = self.post_json('/offers/' + self.test_offer.uuid + '/claim',
                                 data)

        mock_copar.assert_called_once_with(self.context,
                                           'esi_leap:offer:claim',
                                           self.test_offer.uuid,
                                           [statuses.AVAILABLE])
        mock_col.assert_called_once_with(self.context.to_policy_values(),
                                         self.test_offer)
        mock_lease_create.assert_called_once()
        mock_lgdwai.assert_called_once()
        self.assertEqual(http_client.CREATED, request.status_int)

    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.objects.lease.Lease.create')
    @mock.patch('esi_leap.api.controllers.v1.utils.check_offer_lessee')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'check_offer_policy_and_retrieve')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'lease_get_dict_with_added_info')
    def test_claim_parent_lease(self, mock_lgdwai, mock_copar, mock_col,
                                mock_lease_create, mock_generate_uuid):
        lease_uuid = '12345'
        mock_generate_uuid.return_value = lease_uuid
        mock_copar.return_value = self.test_offer_with_parent
        data = {
            'name': 'lease_claim',
            'start_time': '2016-07-16T19:20:30',
            'end_time': '2016-08-16T19:20:30'
        }

        request = self.post_json(
            '/offers/' + self.test_offer_with_parent.uuid + '/claim',
            data)

        mock_copar.assert_called_once_with(self.context,
                                           'esi_leap:offer:claim',
                                           self.test_offer_with_parent.uuid,
                                           [statuses.AVAILABLE])
        mock_col.assert_called_once_with(self.context.to_policy_values(),
                                         self.test_offer_with_parent)
        mock_lease_create.assert_called_once()
        mock_lgdwai.assert_called_once()
        self.assertEqual(http_client.CREATED, request.status_int)

    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'check_offer_policy_and_retrieve')
    @mock.patch('esi_leap.objects.offer.Offer.cancel')
    def test_delete(self, mock_cancel, mock_copar):
        mock_copar.return_value = self.test_offer

        self.delete_json('/offers/' + self.test_offer.uuid)

        mock_copar.assert_called_once_with(self.context,
                                           'esi_leap:offer:delete',
                                           self.test_offer.uuid,
                                           statuses.OFFER_CAN_DELETE)
        mock_cancel.assert_called_once()
