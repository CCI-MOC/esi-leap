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
from oslo_policy import policy
import testtools

from esi_leap.api.controllers.v1.contract import ContractsController
from esi_leap.common import exception
from esi_leap.objects import contract
from esi_leap.tests.api import base as test_api_base


admin_ctx = ctx.RequestContext(project_id='adminid',
                               roles=['admin'])
admin_ctx_dict = admin_ctx.to_policy_values()

owner_ctx = ctx.RequestContext(project_id='ownerid',
                               roles=['owner'])
owner_ctx_dict = owner_ctx.to_policy_values()

lessee_ctx = ctx.RequestContext(project_id="lesseeid",
                                roles=['lessee'])
lessee_ctx_dict = lessee_ctx.to_policy_values()

random_ctx = ctx.RequestContext(project_id='randomid',
                                roles=['randomrole'])
random_ctx_dict = random_ctx.to_policy_values()


def create_test_contract_data():
    return {
        "offer_uuid": "some_uuid",
        "start_time": "2016-07-16T19:20:30",
        "end_time": "2016-08-16T19:20:30"
    }


class TestContractsControllerAdmin(test_api_base.APITestCase):

    def setUp(self):

        self.context = lessee_ctx

        super(TestContractsControllerAdmin, self).setUp()

        o = TestContractsControllerAdmin.create_test_offer(self.context)

        self.test_contract = contract.Contract(
            start_date=datetime.datetime(2016, 7, 16, 19, 20, 30),
            end_date=datetime.datetime(2016, 8, 16, 19, 20, 30),
            uuid='1111111111',
            offer_uuid=o.uuid,
            project_id=lessee_ctx.project_id
        )

    def test_empty(self):
        data = self.get_json('/contracts')
        self.assertEqual([], data['contracts'])

    @mock.patch('esi_leap.objects.contract.Contract.get_all')
    def test_one(self, mock_ga):

        mock_ga.return_value = [self.test_contract]
        data = self.get_json('/contracts')
        self.assertEqual(self.test_contract.uuid,
                         data['contracts'][0]["uuid"])

    @mock.patch('esi_leap.objects.contract.Contract.create')
    def test_post(self, mock_create):

        mock_create.return_value = self.test_contract

        data = create_test_contract_data()
        request = self.post_json('/contracts', data)
        self.assertEqual(1, mock_create.call_count)

        data['project_id'] = lessee_ctx.project_id
        self.assertEqual(request.json, data)
        # FIXME: post returns incorrect status code
        # self.assertEqual(http_client.CREATED, request.status_int)


class TestContractControllersGetAllFilters(testtools.TestCase):

    def test_contract_get_all_no_view_no_projectid_no_owner(self):

        expected_filters = {
            'status': 'random',
            'offer_uuid': 'offeruuid',
        }

        # admin
        expected_filters['project_id'] = admin_ctx_dict['project_id']
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_ctx_dict,
            status='random', offer_uuid='offeruuid')
        self.assertEqual(expected_filters, filters)

        # owner
        expected_filters['project_id'] = owner_ctx.project_id
        filters = ContractsController._contract_get_all_authorize_filters(
            owner_ctx_dict,
            status='random', offer_uuid='offeruuid')
        self.assertEqual(expected_filters, filters)

        # lessee
        expected_filters['project_id'] = lessee_ctx.project_id
        filters = ContractsController._contract_get_all_authorize_filters(
            lessee_ctx_dict,
            status='random', offer_uuid='offeruuid')
        self.assertEqual(expected_filters, filters)

        # random
        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          random_ctx_dict,
                          status='random', offer_uuid='offeruuid')

    def test_contract_get_all_no_view_project_no_owner(self):

        expected_filters = {
            'status': 'random'
        }

        # admin
        expected_filters['project_id'] = admin_ctx_dict['project_id']
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_ctx_dict,
            project_id=admin_ctx_dict['project_id'],
            status='random')
        self.assertEqual(expected_filters, filters)

        expected_filters['project_id'] = random_ctx.project_id
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_ctx_dict,
            project_id=random_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)

        # lessee
        expected_filters['project_id'] = lessee_ctx.project_id
        filters = ContractsController._contract_get_all_authorize_filters(
            lessee_ctx_dict,
            project_id=lessee_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)

        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          lessee_ctx_dict,
                          project_id=random_ctx.project_id,
                          status='random')

        # owner
        expected_filters['project_id'] = owner_ctx.project_id
        filters = ContractsController._contract_get_all_authorize_filters(
            owner_ctx_dict,
            project_id=owner_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)

        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          lessee_ctx_dict,
                          project_id=random_ctx.project_id,
                          status='random')

        # random
        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          random_ctx_dict,
                          project_id=random_ctx.project_id,
                          status='random')

    def test_contract_get_all_no_view_any_projectid_owner(self):

        expected_filters = {
            'status': 'random'
        }

        # admin
        expected_filters['owner'] = admin_ctx_dict['project_id']
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_ctx_dict,
            owner=admin_ctx_dict['project_id'],
            status='random')
        self.assertEqual(expected_filters, filters)

        expected_filters['owner'] = random_ctx.project_id
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_ctx_dict,
            owner=random_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)

        # lessee
        expected_filters['owner'] = lessee_ctx.project_id
        filters = ContractsController._contract_get_all_authorize_filters(
            lessee_ctx_dict,
            owner=lessee_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)

        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          lessee_ctx_dict,
                          owner=random_ctx.project_id,
                          status='random')

        expected_filters['owner'] = lessee_ctx.project_id
        expected_filters['project_id'] = random_ctx.project_id
        filters = ContractsController._contract_get_all_authorize_filters(
            lessee_ctx_dict,
            owner=lessee_ctx.project_id, project_id=random_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)
        del expected_filters['project_id']

        # owner
        expected_filters['owner'] = owner_ctx.project_id
        filters = ContractsController._contract_get_all_authorize_filters(
            owner_ctx_dict,
            owner=owner_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)

        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          lessee_ctx_dict,
                          owner=random_ctx.project_id,
                          status='random')

        expected_filters['owner'] = owner_ctx_dict['project_id']
        expected_filters['project_id'] = random_ctx.project_id
        filters = ContractsController._contract_get_all_authorize_filters(
            owner_ctx_dict,
            owner=owner_ctx.project_id, project_id=random_ctx.project_id,
            status='random')
        self.assertEqual(expected_filters, filters)

        # random
        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          random_ctx_dict,
                          owner=random_ctx.project_id,
                          status='random')

    def test_contract_get_all_all_view(self):

        expected_filters = {
            'status': 'random'
        }

        # admin
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_ctx_dict,
            view='all',
            status='random')
        self.assertEqual(expected_filters, filters)

        # not admin
        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          lessee_ctx_dict,
                          view='all',
                          status='random')

        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          owner_ctx_dict,
                          view='all',
                          status='random')

        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          random_ctx_dict,
                          view='all',
                          status='random')

    def test_contract_get_all_all_view_times(self):

        start = datetime.datetime(2016, 7, 16, 19, 20, 30)
        end = datetime.datetime(2020, 7, 16, 19, 20, 30)

        expected_filters = {
            'status': 'random',
            'start_time': start,
            'end_time': end
        }

        # admin
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_ctx_dict,
            view='all', start_time=start, end_time=end, status='random')
        self.assertEqual(expected_filters, filters)

        self.assertRaises(exception.InvalidTimeAPICommand,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          admin_ctx_dict,
                          view='all', start_time=start, status='random')

        self.assertRaises(exception.InvalidTimeAPICommand,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          admin_ctx_dict,
                          view='all', end_time=end, status='random')

    def test_contract_get_all_status(self):

        expected_filters = {
            'project_id': 'adminid',
            'status': ['created', 'active']
        }

        # admin
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_ctx_dict)
        self.assertEqual(expected_filters, filters)

        del(expected_filters['status'])
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_ctx_dict, status='any')
        self.assertEqual(expected_filters, filters)
