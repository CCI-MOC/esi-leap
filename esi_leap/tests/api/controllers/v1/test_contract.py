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
from esi_leap.common import statuses
from esi_leap.objects import contract
from esi_leap.objects import offer
from esi_leap.resource_objects.test_node import TestNode
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


owner_ctx_2 = ctx.RequestContext(project_id='ownerid2',
                                 roles=['owner'])
lessee_ctx_2 = ctx.RequestContext(project_id="lesseeid2",
                                  roles=['lessee'])


start = datetime.datetime(2016, 7, 16)
start_iso = '2016-07-16T00:00:00'

end = start + datetime.timedelta(days=100)
end_iso = '2016-10-24T00:00:00'


test_node_1 = TestNode('111', owner_ctx.project_id)


def create_test_offer(context):
    o = offer.Offer(
        resource_type='test_node',
        resource_uuid='1234567890',
        uuid='aaaaaaaa',
        start_time=datetime.datetime(2016, 7, 16, 19, 20, 30),
        end_time=datetime.datetime(2016, 8, 16, 19, 20, 30),
        project_id="111111111111"
    )
    o.create(context)
    return o


def create_test_contract(context):
    c = contract.Contract(
        uuid='bbbbbbbb',
        start_date=datetime.datetime(2016, 7, 16, 19, 20, 30),
        end_date=datetime.datetime(2016, 8, 16, 19, 20, 30),
        offer_uuid='1234567890',
        project_id="222222222222"
    )
    c.create(context)
    return c


def create_test_contract_data():
    return {
        "offer_uuid_or_name": "o",
        "start_time": "2016-07-16T19:20:30",
        "end_time": "2016-08-16T19:20:30"
    }


test_offer = offer.Offer(
    resource_type='test_node',
    resource_uuid=test_node_1._uuid,
    name="o",
    uuid='11111',
    status=statuses.AVAILABLE,
    start_time=start,
    end_time=end,
    project_id=owner_ctx.project_id
)

test_contract = contract.Contract(
    offer_uuid="11111",
    name='c',
    uuid='zzzzz',
    project_id=lessee_ctx.project_id,
    status=statuses.CREATED
)

test_contract_2 = contract.Contract(
    offer_uuid="11111",
    name='c',
    uuid='yyyyy',
    project_id=lessee_ctx.project_id,
    status=statuses.CREATED
)

test_contract_3 = contract.Contract(
    offer_uuid="11111",
    name='c',
    uuid='xxxxx',
    project_id=lessee_ctx_2.project_id,
    status=statuses.CREATED
)


test_contract_4 = contract.Contract(
    offer_uuid="11111",
    name='c2',
    uuid='wwwww',
    project_id=lessee_ctx_2.project_id,
    status=statuses.CREATED
)


class TestContractsControllerAdmin(test_api_base.APITestCase):

    def setUp(self):

        self.context = lessee_ctx

        super(TestContractsControllerAdmin, self).setUp()

        o = create_test_offer(self.context)

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

    @mock.patch('esi_leap.api.controllers.v1.contract.uuidutils.generate_uuid')
    @mock.patch('esi_leap.api.controllers.v1.contract.offer.Offer.get')
    @mock.patch('esi_leap.objects.contract.Contract.create')
    def test_post(self, mock_create, mock_offer_get, mock_generate_uuid):

        mock_generate_uuid.return_value = '22222'
        mock_offer_get.return_value = [test_offer]

        data = create_test_contract_data()
        request = self.post_json('/contracts', data)
        self.assertEqual(1, mock_create.call_count)

        data.pop('offer_uuid_or_name')
        data['project_id'] = lessee_ctx.project_id
        data['uuid'] = '22222'
        data['offer_uuid'] = '11111'
        self.assertEqual(request.json, data)
        # FIXME: post returns incorrect status code
        # self.assertEqual(http_client.CREATED, request.status_int)

        mock_generate_uuid.assert_called_once()
        mock_offer_get.assert_called_once_with('o')


class TestContractControllerStaticMethods(testtools.TestCase):

    @mock.patch('esi_leap.api.controllers.v1.contract.offer.Offer.'
                'get_by_uuid')
    @mock.patch('esi_leap.api.controllers.v1.offer.policy.authorize')
    def test__contract_authorize_management_valid_lessee(self,
                                                         mock_authorize,
                                                         mock_gbu):

        ContractsController._contract_authorize_management(
            test_contract, lessee_ctx.to_policy_values()
        )

        assert not mock_authorize.called
        assert not mock_gbu.called

    @mock.patch('esi_leap.api.controllers.v1.contract.offer.Offer.'
                'get_by_uuid')
    @mock.patch('esi_leap.api.controllers.v1.offer.policy.authorize')
    def test__contract_authorize_management_invalid_lessee(self,
                                                           mock_authorize,
                                                           mock_gbu):
        mock_gbu.return_value = test_offer
        mock_authorize.side_effect = [
            policy.PolicyNotAuthorized('esi_leap:contract:contract_admin',
                                       lessee_ctx.to_policy_values(),
                                       lessee_ctx.to_policy_values()),
            policy.PolicyNotAuthorized('esi_leap:offer:offer_admin',
                                       lessee_ctx.to_policy_values(),
                                       lessee_ctx.to_policy_values())
        ]

        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController._contract_authorize_management,
                          test_contract_3, lessee_ctx.to_policy_values())

        mock_authorize.assert_has_calls(
            [
                mock.call('esi_leap:contract:contract_admin',
                          lessee_ctx.to_policy_values(),
                          lessee_ctx.to_policy_values()),
                mock.call('esi_leap:offer:offer_admin',
                          lessee_ctx.to_policy_values(),
                          lessee_ctx.to_policy_values())
            ])

        mock_gbu.assert_called_with(test_contract_3.offer_uuid)

    @mock.patch('esi_leap.api.controllers.v1.contract.offer.Offer.'
                'get_by_uuid')
    @mock.patch('esi_leap.api.controllers.v1.offer.policy.authorize')
    def test__contract_authorize_management_valid_owner(self,
                                                        mock_authorize,
                                                        mock_gbu):

        mock_gbu.return_value = test_offer
        mock_authorize.side_effect = [
            policy.PolicyNotAuthorized('esi_leap:contract:contract_admin',
                                       lessee_ctx.to_policy_values(),
                                       lessee_ctx.to_policy_values()),
            None]

        ContractsController._contract_authorize_management(
            test_contract, owner_ctx.to_policy_values()
        )

        mock_authorize.assert_called_once_with(
            'esi_leap:contract:contract_admin',
            owner_ctx.to_policy_values(),
            owner_ctx.to_policy_values())

        mock_gbu.assert_called_with(test_contract.offer_uuid)

    @mock.patch('esi_leap.api.controllers.v1.contract.offer.Offer.'
                'get_by_uuid')
    @mock.patch('esi_leap.api.controllers.v1.offer.policy.authorize')
    def test__contract_authorize_management_invalid_owner(self,
                                                          mock_authorize,
                                                          mock_gbu):
        mock_gbu.return_value = test_offer
        mock_authorize.side_effect = [
            policy.PolicyNotAuthorized('esi_leap:contract:contract_admin',
                                       owner_ctx_2.to_policy_values(),
                                       owner_ctx_2.to_policy_values()),
            policy.PolicyNotAuthorized('esi_leap:offer:offer_admin',
                                       owner_ctx_2.to_policy_values(),
                                       owner_ctx_2.to_policy_values())
        ]

        self.assertRaises(policy.PolicyNotAuthorized,
                          ContractsController._contract_authorize_management,
                          test_contract_3, owner_ctx_2.to_policy_values())

        mock_authorize.assert_has_calls(
            [
                mock.call('esi_leap:contract:contract_admin',
                          owner_ctx_2.to_policy_values(),
                          owner_ctx_2.to_policy_values()),
                mock.call('esi_leap:offer:offer_admin',
                          owner_ctx_2.to_policy_values(),
                          owner_ctx_2.to_policy_values())
            ])

        mock_gbu.assert_called_with(test_contract_3.offer_uuid)

    @mock.patch('esi_leap.api.controllers.v1.contract.ContractsController.'
                '_contract_authorize_management')
    @mock.patch('esi_leap.api.controllers.v1.contract.contract.Contract.get')
    def test__contract_get_authorized_contract_duplicate(self,
                                                         mock_get,
                                                         mock_cam):
        mock_get.return_value = [
            test_contract, test_contract_2, test_contract_3
        ]
        mock_cam.side_effect = [
            None,
            None,
            policy.PolicyNotAuthorized('esi_leap:offer:contract_admin',
                                       lessee_ctx.to_policy_values(),
                                       lessee_ctx.to_policy_values())
        ]

        self.assertRaises(exception.ContractDuplicateName,
                          ContractsController.
                          _contract_get_authorized_contract,
                          'c',
                          lessee_ctx.to_policy_values())

        mock_get.assert_called_once_with('c')
        mock_cam.assert_has_calls([
            mock.call(test_contract, lessee_ctx.to_policy_values()),
            mock.call(test_contract_2, lessee_ctx.to_policy_values()),
            ])

    @mock.patch('esi_leap.api.controllers.v1.contract.ContractsController.'
                '_contract_authorize_management')
    @mock.patch('esi_leap.api.controllers.v1.contract.contract.Contract.get')
    def test__contract_get_authorized_contract_unique(self,
                                                      mock_get,
                                                      mock_cam):
        mock_get.return_value = [
            test_contract, test_contract_3
        ]
        mock_cam.side_effect = [
            None,
            policy.PolicyNotAuthorized('esi_leap:offer:contract_admin',
                                       lessee_ctx.to_policy_values(),
                                       lessee_ctx.to_policy_values())
        ]

        p = ContractsController._contract_get_authorized_contract(
            'c',
            lessee_ctx.to_policy_values())

        mock_get.assert_called_once_with('c')
        mock_cam.assert_has_calls([
            mock.call(test_contract, lessee_ctx.to_policy_values()),
            mock.call(test_contract_3, lessee_ctx.to_policy_values()),
            ])

        assert p.uuid == test_contract.uuid

    @mock.patch('esi_leap.api.controllers.v1.contract.ContractsController.'
                '_contract_authorize_management')
    @mock.patch('esi_leap.api.controllers.v1.contract.contract.Contract.get')
    def test__contract_get_authorized_contract_none(self,
                                                    mock_get,
                                                    mock_cam):
        mock_get.return_value = [
            test_contract_3
        ]
        mock_cam.side_effect = [
            policy.PolicyNotAuthorized('esi_leap:offer:contract_admin',
                                       lessee_ctx.to_policy_values(),
                                       lessee_ctx.to_policy_values())
        ]

        self.assertRaises(exception.ContractNotFound,
                          ContractsController.
                          _contract_get_authorized_contract,
                          'c',
                          lessee_ctx.to_policy_values())

        mock_get.assert_called_once_with('c')
        mock_cam.assert_has_calls([
            mock.call(test_contract_3, lessee_ctx.to_policy_values()),
            ])


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
