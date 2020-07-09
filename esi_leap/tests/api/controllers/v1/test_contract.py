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


admin_context = ctx.RequestContext()
admin_context.roles = ['admin']
admin_context = admin_context.to_policy_values()
admin_project = 'adminid'

owner_context = ctx.RequestContext()
owner_context.roles = ['owner']
owner_context = owner_context.to_policy_values()
owner_project = "ownerid"

lessee_context = ctx.RequestContext()
lessee_context.roles = ['lessee']
lessee_context = lessee_context.to_policy_values()
lessee_project = 'lesseeid'

admin_owner_context = ctx.RequestContext()
admin_owner_context.roles = ['admin', 'owner']
admin_owner_context = admin_owner_context.to_policy_values()
admin_ownerproject = 'admin_ownerid'

admin_lessee_context = ctx.RequestContext()
admin_lessee_context.roles = ['admin', 'lessee']
admin_lessee_context = admin_lessee_context.to_policy_values()
admin_lesseeproject = 'admin_lesseeid'

owner_lessee_context = ctx.RequestContext()
owner_lessee_context.roles = ['owner', 'lessee']
owner_lessee_context = owner_lessee_context.to_policy_values()
owner_lesseeproject = 'owner_lesseeid'

admin_owner_lessee_context = ctx.RequestContext()
admin_owner_lessee_context.roles = ['admin', 'owner', 'lessee']
admin_owner_lessee_context = admin_owner_lessee_context.to_policy_values()
admin_owner_lesseeproject = 'admin_owner_lesseeid'

random_context = ctx.RequestContext()
random_context.roles = ['randomrole']
random_context = random_context.to_policy_values()
random_project = 'randomid'


def create_test_contract_data():
    return {
        "project_id": "some_id",
        "offer_uuid": "some_uuid",
        "end_time": "2020-07-25T00:00:00"
    }


class TestContractsControllerAdmin(test_api_base.APITestCase):

    def setUp(self):

        super(TestContractsControllerAdmin, self).setUp()

        o = TestContractsControllerAdmin.create_test_offer(self.context)

        self.test_contract = contract.Contract(
            start_date=datetime.datetime(2016, 7, 16, 19, 20, 30),
            end_date=datetime.datetime(2016, 8, 16, 19, 20, 30),
            uuid='1111111111',
            offer_uuid=o.uuid,
            project_id="222222222222"
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
        self.assertEqual(request.json, data)
        # FIXME: post returns incorrect status code
        # self.assertEqual(http_client.CREATED, request.status_int)


class TestContractControllersGetAllFilters(testtools.TestCase):

    def test_contract_get_all_no_view_no_projectid_no_owner(self):

        expected_filters = {
            'status': 'available',
            'offer_uuid': 'offeruuid',
        }

        # admin
        expected_filters['project_id'] = admin_project
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_context, admin_project,
            status='available', offer_uuid='offeruuid')
        self.assertEqual(expected_filters, filters)

        expected_filters['project_id'] = admin_lesseeproject
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_lessee_context, admin_lesseeproject,
            status='available', offer_uuid='offeruuid')
        self.assertEqual(expected_filters, filters)

        # admin owner
        expected_filters['project_id'] = admin_ownerproject
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_owner_context, admin_ownerproject,
            status='available', offer_uuid='offeruuid')
        self.assertEqual(expected_filters, filters)

        # owner lessee
        expected_filters['project_id'] = owner_lesseeproject
        filters = ContractsController._contract_get_all_authorize_filters(
            owner_lessee_context, owner_lesseeproject,
            status='available', offer_uuid='offeruuid')
        self.assertEqual(expected_filters, filters)

        # admin lessee owner
        expected_filters['project_id'] = admin_owner_lesseeproject
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_owner_lessee_context,
            admin_owner_lesseeproject,
            status='available', offer_uuid='offeruuid')
        self.assertEqual(expected_filters, filters)

        # random
        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          random_context, random_project,
                          status='available', offer_uuid='offeruuid')

    def test_contract_get_all_no_view_project_no_owner(self):

        expected_filters = {}

        # admin
        expected_filters['project_id'] = admin_project
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_context, admin_project,
            project_id=admin_project)
        self.assertEqual(expected_filters, filters)

        expected_filters['project_id'] = random_project
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_context, admin_project,
            project_id=random_project)
        self.assertEqual(expected_filters, filters)

        # admin lessee
        expected_filters['project_id'] = admin_lesseeproject
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_lessee_context, admin_lesseeproject,
            project_id=admin_lesseeproject)
        self.assertEqual(expected_filters, filters)

        expected_filters['project_id'] = random_project
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_lessee_context, admin_lesseeproject,
            project_id=random_project)
        self.assertEqual(expected_filters, filters)

        # admin owner
        expected_filters['project_id'] = admin_ownerproject
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_owner_context, admin_ownerproject,
            project_id=admin_ownerproject)
        self.assertEqual(expected_filters, filters)

        expected_filters['project_id'] = random_project
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_owner_context, admin_ownerproject,
            project_id=random_project)
        self.assertEqual(expected_filters, filters)

        # owner lessee
        expected_filters['project_id'] = owner_lesseeproject
        filters = ContractsController._contract_get_all_authorize_filters(
            owner_lessee_context, owner_lesseeproject,
            project_id=owner_lesseeproject)
        self.assertEqual(expected_filters, filters)

        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          owner_lessee_context, owner_lesseeproject,
                          project_id=random_project)

        # admin lessee owner
        expected_filters['project_id'] = admin_owner_lesseeproject
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_owner_lessee_context,
            admin_owner_lesseeproject,
            project_id=admin_owner_lesseeproject)
        self.assertEqual(expected_filters, filters)

        expected_filters['project_id'] = random_project
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_owner_lessee_context,
            admin_owner_lesseeproject,
            project_id=random_project)
        self.assertEqual(expected_filters, filters)

        # random
        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          random_context, random_project,
                          project_id=random_project)

    def test_contract_get_all_no_view_any_projectid_owner(self):

        expected_filters = {}

        # admin
        expected_filters['owner'] = admin_project
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_context, admin_project,
            owner=admin_project)
        self.assertEqual(expected_filters, filters)

        expected_filters['owner'] = random_project
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_context, admin_project,
            owner=random_project)
        self.assertEqual(expected_filters, filters)

        # admin lessee
        expected_filters['owner'] = random_project
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_lessee_context, admin_lesseeproject,
            owner=random_project)
        self.assertEqual(expected_filters, filters)

        # admin owner
        expected_filters['owner'] = random_project
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_owner_context, admin_ownerproject,
            owner=random_project)
        self.assertEqual(expected_filters, filters)

        # owner lessee
        expected_filters['owner'] = owner_lesseeproject
        filters = ContractsController._contract_get_all_authorize_filters(
            owner_lessee_context, owner_lesseeproject,
            owner=owner_lesseeproject)
        self.assertEqual(expected_filters, filters)

        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          owner_lessee_context, owner_lesseeproject,
                          owner=random_project)

        # admin lessee owner
        expected_filters['owner'] = admin_owner_lesseeproject
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_owner_context, admin_owner_lesseeproject,
            owner=admin_owner_lesseeproject)
        self.assertEqual(expected_filters, filters)

        expected_filters['owner'] = random_project
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_owner_context, admin_owner_lesseeproject,
            owner=random_project)
        self.assertEqual(expected_filters, filters)

        # random
        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          random_context, random_project,
                          owner=random_project)

        # owner w/ project_id
        expected_filters['owner'] = owner_project
        expected_filters['project_id'] = random_project
        filters = ContractsController._contract_get_all_authorize_filters(
            owner_context, owner_project,
            owner=owner_project, project_id=random_project)
        self.assertEqual(expected_filters, filters)

    def test_contract_get_all_all_view(self):

        expected_filters = {}

        # admin
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_context, admin_project,
            view='all')
        self.assertEqual(expected_filters, filters)

        # not admin
        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          owner_lessee_context, owner_lesseeproject,
                          view='all')

    def test_contract_get_all_all_view_times(self):

        start = datetime.datetime(2016, 7, 16, 19, 20, 30)
        end = datetime.datetime(2020, 7, 16, 19, 20, 30)

        expected_filters = {
            'start_time': start,
            'end_time': end
        }

        # admin
        filters = ContractsController._contract_get_all_authorize_filters(
            admin_context, admin_project,
            view='all', start_time=start, end_time=end)
        self.assertEqual(expected_filters, filters)

        self.assertRaises(exception.InvalidTimeAPICommand,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          admin_context, admin_project,
                          view='all', start_time=start)

        self.assertRaises(exception.InvalidTimeAPICommand,
                          ContractsController.
                          _contract_get_all_authorize_filters,
                          admin_context, admin_project,
                          view='all', end_time=end)
