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
from oslo_context import context as ctx
from oslo_utils import uuidutils
import testtools

from esi_leap.api.controllers.v1.lease import LeasesController
from esi_leap.common import constants
from esi_leap.common import exception
from esi_leap.common import statuses
from esi_leap.objects import lease as lease_obj
from esi_leap.resource_objects.ironic_node import IronicNode
from esi_leap.resource_objects.test_node import TestNode
from esi_leap.tests.api import base as test_api_base


class TestLeasesController(test_api_base.APITestCase):

    def setUp(self):
        super(TestLeasesController, self).setUp()

        self.test_lease = lease_obj.Lease(
            start_time=datetime.datetime(2016, 7, 16, 19, 20, 30),
            end_time=datetime.datetime(2016, 8, 16, 19, 20, 30),
            uuid=uuidutils.generate_uuid(),
            resource_type='test_node',
            resource_uuid='111',
            project_id='lesseeid',
            owner_id='ownerid',
            parent_lease_uuid=None
        )
        self.test_lease_1 = lease_obj.Lease(
            start_time=datetime.datetime(2016, 7, 16, 19, 20, 30),
            end_time=datetime.datetime(2016, 8, 16, 19, 20, 30),
            uuid=uuidutils.generate_uuid(),
            resource_type='ironic_node',
            resource_uuid='222',
            project_id='lesseeid',
            owner_id='ownerid',
            parent_lease_uuid=None
        )
        self.test_lease_with_parent = lease_obj.Lease(
            start_time=datetime.datetime(2016, 7, 16, 19, 20, 30),
            end_time=datetime.datetime(2016, 8, 16, 19, 20, 30),
            uuid=uuidutils.generate_uuid(),
            resource_type='test_node',
            resource_uuid='111',
            project_id='lesseeid',
            owner_id='ownerid',
            parent_lease_uuid='parent-lease-uuid'
        )

    def test_empty(self):
        data = self.get_json('/leases')
        self.assertEqual([], data['leases'])

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'lease_get_dict_with_added_info')
    @mock.patch('esi_leap.objects.lease.Lease.get_all')
    def test_one(self, mock_ga, mock_lgdwai, mock_gpl, mock_gnl):
        mock_ga.return_value = [self.test_lease]
        mock_lgdwai.return_value = self.test_lease.to_dict()
        mock_gpl.return_value = []
        mock_gnl.return_value = []

        data = self.get_json('/leases')

        self.assertEqual(self.test_lease.uuid,
                         data['leases'][0]['uuid'])
        mock_gpl.assert_called_once()
        mock_gnl.assert_called_once()
        mock_lgdwai.assert_called_once()

    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'lease_get_dict_with_added_info')
    @mock.patch('esi_leap.api.controllers.v1.lease.get_resource_object')
    @mock.patch('esi_leap.common.keystone.get_project_uuid_from_ident')
    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.api.controllers.v1.utils.check_resource_admin')
    @mock.patch('esi_leap.objects.lease.Lease.create')
    def test_post(self, mock_create, mock_cra, mock_generate_uuid,
                  mock_gpufi, mock_gro, mock_lgdwai):
        resource = TestNode('1234567890')
        data = {
            'project_id': 'lesseeid',
            'resource_type': 'test_node',
            'resource_uuid': '1234567890',
            'start_time': '2016-07-16T19:20:30',
            'end_time': '2016-08-16T19:20:30',
            'purpose': 'test_purpose'
        }
        return_data = data.copy()
        return_data['owner_id'] = self.context.project_id
        return_data['uuid'] = self.test_lease.uuid
        lgdwai_return_data = return_data.copy()
        lgdwai_return_data['start_time'] = datetime.datetime(
            2016, 7, 16, 19, 20, 30)
        lgdwai_return_data['end_time'] = datetime.datetime(
            2016, 8, 16, 19, 20, 30)

        mock_gro.return_value = resource
        mock_gpufi.return_value = 'lesseeid'
        mock_generate_uuid.return_value = self.test_lease.uuid
        mock_lgdwai.return_value = lgdwai_return_data

        request = self.post_json('/leases', data)

        mock_gro.assert_called_once_with('test_node', '1234567890')
        mock_generate_uuid.assert_called_once()
        mock_cra.assert_called_once_with(
            self.context.to_policy_values(),
            resource,
            self.context.project_id)
        mock_create.assert_called_once()
        mock_lgdwai.assert_called_once()
        self.assertEqual(return_data, request.json)
        self.assertEqual(http_client.CREATED, request.status_int)

    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'lease_get_dict_with_added_info')
    @mock.patch('esi_leap.api.controllers.v1.lease.get_resource_object')
    @mock.patch('esi_leap.common.keystone.get_project_uuid_from_ident')
    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.api.controllers.v1.utils.check_resource_admin')
    @mock.patch('esi_leap.objects.lease.Lease.create')
    def test_post_default_resource_type(self, mock_create, mock_cra,
                                        mock_generate_uuid, mock_gpufi,
                                        mock_gro, mock_lgdwai):
        resource = IronicNode('13921c8d-ce11-4b6d-99ed-10e19d184e5f')
        data = {
            'project_id': 'lesseeid',
            'resource_uuid': '1234567890',
            'start_time': '2016-07-16T19:20:30',
            'end_time': '2016-08-16T19:20:30'
        }
        return_data = data.copy()
        return_data['resource_type'] = 'ironic_node'
        return_data['owner_id'] = self.context.project_id
        return_data['uuid'] = self.test_lease.uuid
        lgdwai_return_data = return_data.copy()
        lgdwai_return_data['start_time'] = datetime.datetime(
            2016, 7, 16, 19, 20, 30)
        lgdwai_return_data['end_time'] = datetime.datetime(
            2016, 8, 16, 19, 20, 30)

        mock_gro.return_value = resource
        mock_gpufi.return_value = 'lesseeid'
        mock_generate_uuid.return_value = self.test_lease.uuid
        mock_lgdwai.return_value = lgdwai_return_data

        request = self.post_json('/leases', data)

        mock_gro.assert_called_once_with('ironic_node', '1234567890')
        mock_generate_uuid.assert_called_once()
        mock_cra.assert_called_once_with(
            self.context.to_policy_values(),
            resource,
            self.context.project_id)
        mock_create.assert_called_once()
        mock_lgdwai.assert_called_once()
        self.assertEqual(return_data, request.json)
        self.assertEqual(http_client.CREATED, request.status_int)

    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'lease_get_dict_with_added_info')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'check_resource_lease_admin')
    @mock.patch('esi_leap.api.controllers.v1.lease.get_resource_object')
    @mock.patch('esi_leap.common.keystone.get_project_uuid_from_ident')
    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.api.controllers.v1.utils.check_resource_admin')
    @mock.patch('esi_leap.objects.lease.Lease.create')
    def test_post_non_admin_parent_lease(self, mock_create, mock_cra,
                                         mock_generate_uuid, mock_gpufi,
                                         mock_gro, mock_crla, mock_lgdwai):
        resource = IronicNode('13921c8d-ce11-4b6d-99ed-10e19d184e5f')
        data = {
            'project_id': 'lesseeid',
            'resource_uuid': '1234567890',
            'start_time': '2016-07-17T19:20:30',
            'end_time': '2016-08-14T19:20:30'
        }
        return_data = data.copy()
        return_data['owner_id'] = self.context.project_id
        return_data['uuid'] = self.test_lease_with_parent.uuid
        return_data['resource_type'] = 'ironic_node'
        return_data['parent_lease_uuid'] = (
            self.test_lease_with_parent.parent_lease_uuid)
        lgdwai_return_data = return_data.copy()
        lgdwai_return_data['start_time'] = datetime.datetime(
            2016, 7, 17, 19, 20, 30)
        lgdwai_return_data['end_time'] = datetime.datetime(
            2016, 8, 14, 19, 20, 30)

        mock_gro.return_value = resource
        mock_gpufi.return_value = 'lesseeid'
        mock_generate_uuid.return_value = self.test_lease_with_parent.uuid
        mock_cra.side_effect = exception.HTTPResourceForbidden(
            resource_type='ironic_node', resource='1234567890')
        mock_crla.return_value = self.test_lease_with_parent.parent_lease_uuid
        mock_lgdwai.return_value = lgdwai_return_data

        request = self.post_json('/leases', data)

        mock_gro.assert_called_once_with('ironic_node', '1234567890')
        mock_generate_uuid.assert_called_once()
        mock_cra.assert_called_once_with(
            self.context.to_policy_values(),
            resource,
            self.context.project_id)
        mock_crla.assert_called_once_with(
            self.context.to_policy_values(),
            resource,
            self.context.project_id,
            datetime.datetime(2016, 7, 17, 19, 20, 30),
            datetime.datetime(2016, 8, 14, 19, 20, 30))
        mock_create.assert_called_once()
        mock_lgdwai.assert_called_once()
        self.assertEqual(return_data, request.json)
        self.assertEqual(http_client.CREATED, request.status_int)

    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'check_resource_lease_admin')
    @mock.patch('esi_leap.api.controllers.v1.lease.get_resource_object')
    @mock.patch('esi_leap.common.keystone.get_project_uuid_from_ident')
    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.api.controllers.v1.utils.check_resource_admin')
    @mock.patch('esi_leap.objects.lease.Lease.create')
    def test_post_non_admin_no_parent_lease(self, mock_create, mock_cra,
                                            mock_generate_uuid, mock_gpufi,
                                            mock_gro, mock_crla):
        fake_uuid = '13921c8d-ce11-4b6d-99ed-10e19d184e5f'
        resource = IronicNode(fake_uuid)
        mock_gro.return_value = resource
        mock_gpufi.return_value = 'lesseeid'
        mock_generate_uuid.return_value = self.test_lease.uuid
        mock_cra.side_effect = exception.HTTPResourceForbidden(
            resource_type='ironic_node', resource=fake_uuid)
        mock_crla.return_value = None

        data = {
            'project_id': 'lesseeid',
            'resource_uuid': fake_uuid,
            'start_time': '2016-07-17T19:20:30',
            'end_time': '2016-08-14T19:20:30'
        }
        request = self.post_json('/leases', data, expect_errors=True)

        mock_gro.assert_called_once_with('ironic_node', fake_uuid)
        mock_generate_uuid.assert_called_once()
        mock_cra.assert_called_once_with(
            self.context.to_policy_values(),
            resource,
            self.context.project_id)
        mock_crla.assert_called_once_with(
            self.context.to_policy_values(),
            resource,
            self.context.project_id,
            datetime.datetime(2016, 7, 17, 19, 20, 30),
            datetime.datetime(2016, 8, 14, 19, 20, 30))
        mock_create.assert_not_called()
        self.assertEqual(http_client.FORBIDDEN, request.status_int)

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'lease_get_dict_with_added_info')
    @mock.patch('esi_leap.api.controllers.v1.lease.LeasesController.'
                '_lease_get_all_authorize_filters')
    @mock.patch('esi_leap.objects.lease.Lease.get_all')
    def test_get_nofilters(self, mock_get_all, mock_lgaaf, mock_lgdwai,
                           mock_gpl, mock_gnl):
        mock_get_all.return_value = [self.test_lease, self.test_lease]
        mock_gpl.return_value = []
        mock_gnl.return_value = []

        self.get_json('/leases')

        mock_lgaaf.assert_called_once_with(self.context.to_policy_values(),
                                           project_id=None,
                                           start_time=None,
                                           end_time=None,
                                           status=None,
                                           offer_uuid=None,
                                           view=None,
                                           owner_id=None,
                                           resource_type=None,
                                           resource_uuid=None)
        mock_get_all.assert_called_once()
        mock_gpl.assert_called_once()
        mock_gnl.assert_called_once()
        self.assertEqual(2, mock_lgdwai.call_count)

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'lease_get_dict_with_added_info')
    @mock.patch('esi_leap.common.keystone.get_project_uuid_from_ident')
    @mock.patch('esi_leap.api.controllers.v1.lease.LeasesController.'
                '_lease_get_all_authorize_filters')
    @mock.patch('esi_leap.objects.lease.Lease.get_all')
    def test_get_project_filter(self, mock_get_all, mock_lgaaf,
                                mock_gpufi, mock_lgdwai, mock_gpl,
                                mock_gnl):
        mock_gpufi.return_value = '12345'
        mock_get_all.return_value = [self.test_lease, self.test_lease]
        mock_gpl.return_value = []
        mock_gnl.return_value = []
        self.get_json('/leases?project_id=12345')

        mock_gpufi.assert_called_once_with('12345')
        mock_lgaaf.assert_called_once_with(self.context.to_policy_values(),
                                           project_id='12345',
                                           start_time=None,
                                           end_time=None,
                                           status=None,
                                           offer_uuid=None,
                                           view=None,
                                           owner_id=None,
                                           resource_type=None,
                                           resource_uuid=None)
        mock_get_all.assert_called_once()
        mock_gpl.assert_called_once()
        mock_gnl.assert_called_once()
        self.assertEqual(2, mock_lgdwai.call_count)

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'lease_get_dict_with_added_info')
    @mock.patch('esi_leap.common.keystone.get_project_uuid_from_ident')
    @mock.patch('esi_leap.api.controllers.v1.lease.LeasesController.'
                '_lease_get_all_authorize_filters')
    @mock.patch('esi_leap.objects.lease.Lease.get_all')
    def test_get_owner_filter(self, mock_get_all, mock_lgaaf,
                              mock_gpufi, mock_lgdwai, mock_gpl,
                              mock_gnl):
        mock_gpufi.return_value = '54321'
        mock_get_all.return_value = [self.test_lease, self.test_lease]
        mock_gpl.return_value = []
        mock_gnl.return_value = []

        self.get_json('/leases?owner_id=54321')

        mock_gpufi.assert_called_once_with('54321')
        mock_lgaaf.assert_called_once_with(self.context.to_policy_values(),
                                           project_id=None,
                                           start_time=None,
                                           end_time=None,
                                           status=None,
                                           offer_uuid=None,
                                           view=None,
                                           owner_id='54321',
                                           resource_type=None,
                                           resource_uuid=None)

        mock_get_all.assert_called_once()
        mock_gpl.assert_called_once()
        mock_gnl.assert_called_once()
        self.assertEqual(2, mock_lgdwai.call_count)

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'lease_get_dict_with_added_info')
    @mock.patch('esi_leap.api.controllers.v1.lease.get_resource_object')
    @mock.patch('esi_leap.api.controllers.v1.lease.LeasesController.'
                '_lease_get_all_authorize_filters')
    @mock.patch('esi_leap.objects.lease.Lease.get_all')
    def test_get_resource_filter(self, mock_get_all, mock_lgaaf,
                                 mock_gro, mock_lgdwai, mock_gpl,
                                 mock_gnl):
        mock_gro.return_value = TestNode('54321')
        mock_get_all.return_value = [self.test_lease, self.test_lease]
        mock_gpl.return_value = []
        mock_gnl.return_value = []

        self.get_json('/leases?resource_uuid=54321&resource_type=test_node')

        mock_gro.assert_called_once_with('test_node', '54321')
        mock_lgaaf.assert_called_once_with(self.context.to_policy_values(),
                                           project_id=None,
                                           start_time=None,
                                           end_time=None,
                                           status=None,
                                           offer_uuid=None,
                                           view=None,
                                           owner_id=None,
                                           resource_type='test_node',
                                           resource_uuid='54321')

        mock_get_all.assert_called_once()
        mock_gpl.assert_called_once()
        mock_gnl.assert_called_once()
        self.assertEqual(2, mock_lgdwai.call_count)

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'lease_get_dict_with_added_info')
    @mock.patch('esi_leap.api.controllers.v1.lease.LeasesController.'
                '_lease_get_all_authorize_filters')
    @mock.patch('esi_leap.objects.lease.Lease.get_all')
    def test_get_resource_class_filter(self, mock_get_all, mock_lgaaf,
                                       mock_lgdwai, mock_gpl, mock_gnl):
        def _get_lease_response(l, use_datetime=False):
            if use_datetime:
                start = datetime.datetime(2016, 7, 16, 19, 20, 30)
                end = datetime.datetime(2016, 8, 16, 19, 20, 30)
            else:
                start = '2016-07-16T19:20:30'
                end = '2016-08-16T19:20:30'

            if l.resource_type in ['test_node', 'dummy_node']:
                resource_class = 'fake'
            elif l.resource_type == 'ironic_node':
                resource_class = 'baremetal'

            return {
                'resource_type': l.resource_type,
                'resource_uuid': l.resource_uuid,
                'resource_class': resource_class,
                'project_id': l.project_id,
                'start_time': start,
                'end_time': end,
                'uuid': l.uuid,
                'owner_id': l.owner_id,
                'parent_lease_uuid': None
            }

        mock_get_all.return_value = [self.test_lease, self.test_lease]
        mock_gpl.return_value = []
        mock_gnl.return_value = []
        mock_lgdwai.side_effect = [_get_lease_response(self.test_lease,
                                                       use_datetime=True),
                                   _get_lease_response(self.test_lease_1,
                                                       use_datetime=True)]
        response = self.get_json('/leases?resource_class=fake')

        expected_resp = {'leases': [_get_lease_response(self.test_lease)]}

        mock_lgaaf.assert_called_once_with(self.context.to_policy_values(),
                                           project_id=None,
                                           start_time=None,
                                           end_time=None,
                                           status=None,
                                           offer_uuid=None,
                                           view=None,
                                           owner_id=None,
                                           resource_type=None,
                                           resource_uuid=None)

        mock_get_all.assert_called_once()
        mock_gpl.assert_called_once()
        mock_gnl.assert_called_once()
        self.assertEqual(2, mock_lgdwai.call_count)
        self.assertEqual(response, expected_resp)

    @mock.patch('esi_leap.common.ironic.get_node_list')
    @mock.patch('esi_leap.common.keystone.get_project_list')
    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'lease_get_dict_with_added_info')
    @mock.patch('esi_leap.api.controllers.v1.lease.get_resource_object')
    @mock.patch('esi_leap.api.controllers.v1.lease.LeasesController.'
                '_lease_get_all_authorize_filters')
    @mock.patch('esi_leap.objects.lease.Lease.get_all')
    def test_get_resource_filter_default_resource_type(self, mock_get_all,
                                                       mock_lgaaf, mock_gro,
                                                       mock_lgdwai, mock_gpl,
                                                       mock_gnl):
        fake_uuid = uuidutils.generate_uuid()
        mock_gro.return_value = IronicNode(fake_uuid)
        mock_get_all.return_value = [self.test_lease, self.test_lease]
        mock_gpl.return_value = []
        mock_gnl.return_value = []

        self.get_json('/leases?resource_uuid=%s' % fake_uuid)

        mock_gro.assert_called_once_with('ironic_node', fake_uuid)
        mock_lgaaf.assert_called_once_with(self.context.to_policy_values(),
                                           project_id=None,
                                           start_time=None,
                                           end_time=None,
                                           status=None,
                                           offer_uuid=None,
                                           view=None,
                                           owner_id=None,
                                           resource_type='ironic_node',
                                           resource_uuid=fake_uuid)

        mock_get_all.assert_called_once()
        mock_gpl.assert_called_once()
        mock_gnl.assert_called_once()
        self.assertEqual(2, mock_lgdwai.call_count)

    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'check_lease_policy_and_retrieve')
    @mock.patch('esi_leap.objects.lease.Lease.cancel')
    def test_lease_delete(self, mock_cancel, mock_clpar):
        mock_clpar.return_value = self.test_lease

        self.delete_json('/leases/' + self.test_lease.uuid)

        mock_clpar.assert_called_once_with(self.context,
                                           'esi_leap:lease:get',
                                           self.test_lease.uuid,
                                           statuses.LEASE_CAN_DELETE)
        mock_cancel.assert_called_once()


class TestLeaseControllersGetAllFilters(testtools.TestCase):

    def setUp(self):
        super(TestLeaseControllersGetAllFilters, self).setUp()

        self.admin_ctx = ctx.RequestContext(project_id='adminid',
                                            roles=['admin'])
        self.owner_ctx = ctx.RequestContext(project_id='ownerid',
                                            roles=['owner'])
        self.lessee_ctx = ctx.RequestContext(project_id='lesseeid',
                                             roles=['lessee'])
        self.random_ctx = ctx.RequestContext(project_id='randomid',
                                             roles=['randomrole'])

    def test_lease_get_all_no_view_no_projectid_no_owner(self):

        expected_filters = {
            'status': ['random'],
            'offer_uuid': 'offeruuid',
            'time_filter_type': constants.WITHIN_TIME_FILTER
        }

        # admin
        expected_filters['project_or_owner_id'] = self.admin_ctx.project_id
        filters = LeasesController._lease_get_all_authorize_filters(
            self.admin_ctx.to_policy_values(),
            status='random', offer_uuid='offeruuid')
        self.assertEqual(expected_filters, filters)

        # owner
        expected_filters['project_or_owner_id'] = self.owner_ctx.project_id
        filters = LeasesController._lease_get_all_authorize_filters(
            self.owner_ctx.to_policy_values(),
            status='random', offer_uuid='offeruuid')
        self.assertEqual(expected_filters, filters)

        # lessee
        expected_filters['project_or_owner_id'] = self.lessee_ctx.project_id
        filters = LeasesController._lease_get_all_authorize_filters(
            self.lessee_ctx.to_policy_values(),
            status='random', offer_uuid='offeruuid')
        self.assertEqual(expected_filters, filters)

        # random
        self.assertRaises(exception.HTTPForbidden,
                          LeasesController.
                          _lease_get_all_authorize_filters,
                          self.random_ctx.to_policy_values(),
                          status='random', offer_uuid='offeruuid')

    def test_lease_get_all_no_view_project_no_owner(self):

        expected_filters = {
            'status': ['random'],
            'time_filter_type': constants.WITHIN_TIME_FILTER
        }

        # admin
        expected_filters['project_id'] = self.admin_ctx.project_id
        filters = LeasesController._lease_get_all_authorize_filters(
            self.admin_ctx.to_policy_values(),
            project_id=self.admin_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)

        # lessee
        expected_filters['project_id'] = self.lessee_ctx.project_id
        filters = LeasesController._lease_get_all_authorize_filters(
            self.lessee_ctx.to_policy_values(),
            project_id=self.lessee_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)

        self.assertRaises(exception.HTTPForbidden,
                          LeasesController.
                          _lease_get_all_authorize_filters,
                          self.random_ctx.to_policy_values(),
                          project_id=self.random_ctx.project_id,
                          status='random')

        # owner
        expected_filters['project_id'] = self.owner_ctx.project_id
        filters = LeasesController._lease_get_all_authorize_filters(
            self.owner_ctx.to_policy_values(),
            project_id=self.owner_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)

        # random
        self.assertRaises(exception.HTTPForbidden,
                          LeasesController.
                          _lease_get_all_authorize_filters,
                          self.random_ctx.to_policy_values(),
                          project_id=self.random_ctx.project_id,
                          status='random')

    def test_lease_get_all_no_view_any_projectid_owner(self):

        expected_filters = {
            'status': ['random'],
            'time_filter_type': constants.WITHIN_TIME_FILTER
        }

        # admin
        expected_filters['owner_id'] = self.admin_ctx.project_id
        filters = LeasesController._lease_get_all_authorize_filters(
            self.admin_ctx.to_policy_values(),
            owner_id=self.admin_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)

        # lessee
        expected_filters['owner_id'] = self.lessee_ctx.project_id
        filters = LeasesController._lease_get_all_authorize_filters(
            self.lessee_ctx.to_policy_values(),
            owner_id=self.lessee_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)

        expected_filters['owner_id'] = self.lessee_ctx.project_id
        expected_filters['project_id'] = self.random_ctx.project_id
        filters = LeasesController._lease_get_all_authorize_filters(
            self.lessee_ctx.to_policy_values(),
            owner_id=self.lessee_ctx.project_id,
            project_id=self.random_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)
        del expected_filters['project_id']

        # owner
        expected_filters['owner_id'] = self.owner_ctx.project_id
        filters = LeasesController._lease_get_all_authorize_filters(
            self.owner_ctx.to_policy_values(),
            owner_id=self.owner_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)

        expected_filters['owner_id'] = self.owner_ctx.project_id
        expected_filters['project_id'] = self.random_ctx.project_id
        filters = LeasesController._lease_get_all_authorize_filters(
            self.owner_ctx.to_policy_values(),
            owner_id=self.owner_ctx.project_id,
            project_id=self.random_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)

        # random
        self.assertRaises(exception.HTTPForbidden,
                          LeasesController.
                          _lease_get_all_authorize_filters,
                          self.random_ctx.to_policy_values(),
                          owner_id=self.random_ctx.project_id,
                          status='random')

    def test_lease_get_all_all_view(self):

        expected_filters = {
            'status': ['random'],
            'time_filter_type': constants.WITHIN_TIME_FILTER
        }

        # admin
        filters = LeasesController._lease_get_all_authorize_filters(
            self.admin_ctx.to_policy_values(),
            view='all',
            status='random')
        self.assertEqual(expected_filters, filters)

        # not admin
        self.assertRaises(exception.HTTPForbidden,
                          LeasesController.
                          _lease_get_all_authorize_filters,
                          self.lessee_ctx.to_policy_values(),
                          view='all',
                          status='random')

        self.assertRaises(exception.HTTPForbidden,
                          LeasesController.
                          _lease_get_all_authorize_filters,
                          self.owner_ctx.to_policy_values(),
                          view='all',
                          status='random')

        self.assertRaises(exception.HTTPForbidden,
                          LeasesController.
                          _lease_get_all_authorize_filters,
                          self.random_ctx.to_policy_values(),
                          view='all',
                          status='random')

    def test_lease_get_all_all_view_times(self):

        start = datetime.datetime(2016, 7, 16, 19, 20, 30)
        end = datetime.datetime(2020, 7, 16, 19, 20, 30)

        expected_filters = {
            'status': ['random'],
            'start_time': start,
            'end_time': end,
            'time_filter_type': constants.WITHIN_TIME_FILTER
        }

        # admin
        filters = LeasesController._lease_get_all_authorize_filters(
            self.admin_ctx.to_policy_values(),
            view='all', start_time=start, end_time=end, status='random')
        self.assertEqual(expected_filters, filters)

        self.assertRaises(exception.InvalidTimeAPICommand,
                          LeasesController.
                          _lease_get_all_authorize_filters,
                          self.admin_ctx.to_policy_values(),
                          view='all', start_time=start, status='random')

        self.assertRaises(exception.InvalidTimeAPICommand,
                          LeasesController.
                          _lease_get_all_authorize_filters,
                          self.admin_ctx.to_policy_values(),
                          view='all', end_time=end, status='random')

    def test_lease_get_all_status(self):

        expected_filters = {
            'project_or_owner_id': 'adminid',
            'status': [statuses.CREATED, statuses.ACTIVE, statuses.ERROR,
                       statuses.WAIT_CANCEL, statuses.WAIT_EXPIRE,
                       statuses.WAIT_FULFILL],
            'time_filter_type': constants.WITHIN_TIME_FILTER
        }

        # admin
        filters = LeasesController._lease_get_all_authorize_filters(
            self.admin_ctx.to_policy_values())
        self.assertEqual(expected_filters, filters)

        del(expected_filters['status'])
        filters = LeasesController._lease_get_all_authorize_filters(
            self.admin_ctx.to_policy_values(), status='any')
        self.assertEqual(expected_filters, filters)
