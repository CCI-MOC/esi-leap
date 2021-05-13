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
from oslo_policy import policy
from oslo_utils import uuidutils
import testtools

from esi_leap.api.controllers.v1.lease import LeasesController
from esi_leap.common import exception
from esi_leap.objects import lease as lease_obj
from esi_leap.tests.api import base as test_api_base


class TestLeasesController(test_api_base.APITestCase):

    def setUp(self):
        super(TestLeasesController, self).setUp()

        self.test_lease = lease_obj.Lease(
            start_date=datetime.datetime(2016, 7, 16, 19, 20, 30),
            end_date=datetime.datetime(2016, 8, 16, 19, 20, 30),
            uuid=uuidutils.generate_uuid(),
            resource_type='test_node',
            resource_uuid='111',
            project_id='lesseeid',
            owner_id='ownerid'
        )

    def test_empty(self):
        data = self.get_json('/leases')
        self.assertEqual([], data['leases'])

    @mock.patch('esi_leap.objects.lease.Lease.get_all')
    def test_one(self, mock_ga):
        mock_ga.return_value = [self.test_lease]
        data = self.get_json('/leases')
        self.assertEqual(self.test_lease.uuid,
                         data['leases'][0]["uuid"])

    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.api.controllers.v1.utils.check_resource_admin')
    @mock.patch('esi_leap.objects.lease.Lease.create')
    def test_post(self, mock_create, mock_cra, mock_generate_uuid):
        mock_generate_uuid.return_value = self.test_lease.uuid

        data = {
            "project_id": "lesseeid",
            "resource_type": "test_node",
            "resource_uuid": "1234567890",
            "start_time": "2016-07-16T19:20:30",
            "end_time": "2016-08-16T19:20:30"
        }
        request = self.post_json('/leases', data)

        data['owner_id'] = self.context.project_id
        data['uuid'] = self.test_lease.uuid

        mock_generate_uuid.assert_called_once()
        mock_cra.assert_called_once_with(
            self.context.to_policy_values(),
            'test_node', '1234567890',
            self.context.project_id,
            datetime.datetime(2016, 7, 16, 19, 20, 30),
            datetime.datetime(2016, 8, 16, 19, 20, 30))
        mock_create.assert_called_once()
        self.assertEqual(data, request.json)
        self.assertEqual(http_client.CREATED, request.status_int)

    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.api.controllers.v1.utils.check_resource_admin')
    @mock.patch('esi_leap.objects.lease.Lease.create')
    def test_post_default_resource_type(self, mock_create, mock_cra,
                                        mock_generate_uuid):
        mock_generate_uuid.return_value = self.test_lease.uuid

        data = {
            "project_id": "lesseeid",
            "resource_uuid": "1234567890",
            "start_time": "2016-07-16T19:20:30",
            "end_time": "2016-08-16T19:20:30"
        }
        request = self.post_json('/leases', data)

        data['owner_id'] = self.context.project_id
        data['uuid'] = self.test_lease.uuid
        data['resource_type'] = 'ironic_node'

        mock_generate_uuid.assert_called_once()
        mock_cra.assert_called_once_with(
            self.context.to_policy_values(),
            'ironic_node', '1234567890',
            self.context.project_id,
            datetime.datetime(2016, 7, 16, 19, 20, 30),
            datetime.datetime(2016, 8, 16, 19, 20, 30))
        mock_create.assert_called_once()
        self.assertEqual(data, request.json)
        self.assertEqual(http_client.CREATED, request.status_int)


class TestLeaseControllersGetAllFilters(testtools.TestCase):

    def setUp(self):
        super(TestLeaseControllersGetAllFilters, self).setUp()

        self.admin_ctx = ctx.RequestContext(project_id='adminid',
                                            roles=['admin'])
        self.owner_ctx = ctx.RequestContext(project_id='ownerid',
                                            roles=['owner'])
        self.lessee_ctx = ctx.RequestContext(project_id="lesseeid",
                                             roles=['lessee'])
        self.random_ctx = ctx.RequestContext(project_id='randomid',
                                             roles=['randomrole'])

    def test_lease_get_all_no_view_no_projectid_no_owner(self):

        expected_filters = {
            'status': ['random'],
            'offer_uuid': 'offeruuid',
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
        self.assertRaises(policy.PolicyNotAuthorized,
                          LeasesController.
                          _lease_get_all_authorize_filters,
                          self.random_ctx.to_policy_values(),
                          status='random', offer_uuid='offeruuid')

    def test_lease_get_all_no_view_project_no_owner(self):

        expected_filters = {
            'status': ['random']
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

        self.assertRaises(policy.PolicyNotAuthorized,
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
        self.assertRaises(policy.PolicyNotAuthorized,
                          LeasesController.
                          _lease_get_all_authorize_filters,
                          self.random_ctx.to_policy_values(),
                          project_id=self.random_ctx.project_id,
                          status='random')

    def test_lease_get_all_no_view_any_projectid_owner(self):

        expected_filters = {
            'status': ['random']
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
        self.assertRaises(policy.PolicyNotAuthorized,
                          LeasesController.
                          _lease_get_all_authorize_filters,
                          self.random_ctx.to_policy_values(),
                          owner_id=self.random_ctx.project_id,
                          status='random')

    def test_lease_get_all_all_view(self):

        expected_filters = {
            'status': ['random']
        }

        # admin
        filters = LeasesController._lease_get_all_authorize_filters(
            self.admin_ctx.to_policy_values(),
            view='all',
            status='random')
        self.assertEqual(expected_filters, filters)

        # not admin
        self.assertRaises(policy.PolicyNotAuthorized,
                          LeasesController.
                          _lease_get_all_authorize_filters,
                          self.lessee_ctx.to_policy_values(),
                          view='all',
                          status='random')

        self.assertRaises(policy.PolicyNotAuthorized,
                          LeasesController.
                          _lease_get_all_authorize_filters,
                          self.owner_ctx.to_policy_values(),
                          view='all',
                          status='random')

        self.assertRaises(policy.PolicyNotAuthorized,
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
            'end_time': end
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
            'status': ['created', 'active']
        }

        # admin
        filters = LeasesController._lease_get_all_authorize_filters(
            self.admin_ctx.to_policy_values())
        self.assertEqual(expected_filters, filters)

        del(expected_filters['status'])
        filters = LeasesController._lease_get_all_authorize_filters(
            self.admin_ctx.to_policy_values(), status='any')
        self.assertEqual(expected_filters, filters)
