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
from oslo_utils import uuidutils

import testtools

from esi_leap.api.controllers.v1 import utils
from esi_leap.common import exception
from esi_leap.common import statuses
from esi_leap.objects import contract
from esi_leap.objects import offer
from esi_leap.resource_objects.test_node import TestNode


admin_ctx = ctx.RequestContext(project_id='adminid',
                               roles=['admin'])

owner_ctx = ctx.RequestContext(project_id='ownerid',
                               roles=['owner'])
owner_ctx_dict = owner_ctx.to_policy_values()

lessee_ctx = ctx.RequestContext(project_id="lesseeid",
                                roles=['lessee'])
lessee_ctx_dict = lessee_ctx.to_policy_values()

owner_ctx_2 = ctx.RequestContext(project_id='ownerid2',
                                 roles=['owner'])
lessee_ctx_2 = ctx.RequestContext(project_id="lesseeid2",
                                  roles=['lessee'])


start = datetime.datetime(2016, 7, 16)
start_iso = '2016-07-16T00:00:00'

end = start + datetime.timedelta(days=100)
end_iso = '2016-10-24T00:00:00'

test_node_1 = TestNode('111', owner_ctx.project_id)
test_node_2 = TestNode('bbb', owner_ctx_2.project_id)

o_uuid = uuidutils.generate_uuid()


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
    name="o",
    uuid=uuidutils.generate_uuid(),
    status=statuses.EXPIRED,
    start_time=start,
    end_time=end,
    project_id=owner_ctx.project_id
)

test_contract = contract.Contract(
    offer_uuid=o_uuid,
    name='c',
    uuid=uuidutils.generate_uuid(),
    project_id=lessee_ctx.project_id,
    status=statuses.CREATED
)

test_contract_2 = contract.Contract(
    offer_uuid=o_uuid,
    name='c',
    uuid=uuidutils.generate_uuid(),
    project_id=lessee_ctx.project_id,
    status=statuses.CREATED
)

test_contract_3 = contract.Contract(
    offer_uuid=o_uuid,
    name='c',
    uuid=uuidutils.generate_uuid(),
    project_id=lessee_ctx_2.project_id,
    status=statuses.CREATED
)

test_contract_4 = contract.Contract(
    offer_uuid=o_uuid,
    name='c2',
    uuid=uuidutils.generate_uuid(),
    project_id=lessee_ctx_2.project_id,
    status=statuses.CREATED
)


class TestManagementUtils(testtools.TestCase):

    @mock.patch('esi_leap.api.controllers.v1.utils.offer.Offer.get')
    @mock.patch('esi_leap.api.controllers.v1.utils.policy.authorize')
    def test__contract_authorize_management_valid_lessee(self,
                                                         mock_authorize,
                                                         mock_get):
        utils.contract_authorize_management(
            test_contract, lessee_ctx.to_policy_values()
        )

        assert not mock_authorize.called
        assert not mock_get.called

    @mock.patch('esi_leap.api.controllers.v1.utils.offer.Offer.get')
    @mock.patch('esi_leap.api.controllers.v1.utils.policy.authorize')
    def test__contract_authorize_management_invalid_lessee(self,
                                                           mock_authorize,
                                                           mock_get):
        mock_get.return_value = test_offer
        mock_authorize.side_effect = [
            policy.PolicyNotAuthorized('esi_leap:contract:contract_admin',
                                       lessee_ctx.to_policy_values(),
                                       lessee_ctx.to_policy_values()),
            policy.PolicyNotAuthorized('esi_leap:offer:offer_admin',
                                       lessee_ctx.to_policy_values(),
                                       lessee_ctx.to_policy_values())
        ]

        self.assertRaises(policy.PolicyNotAuthorized,
                          utils.contract_authorize_management,
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

        mock_get.assert_called_with(test_contract_3.offer_uuid)

    @mock.patch('esi_leap.api.controllers.v1.utils.offer.Offer.get')
    @mock.patch('esi_leap.api.controllers.v1.utils.policy.authorize')
    def test__contract_authorize_management_valid_owner(self,
                                                        mock_authorize,
                                                        mock_get):
        mock_get.return_value = test_offer
        mock_authorize.side_effect = [
            policy.PolicyNotAuthorized('esi_leap:contract:contract_admin',
                                       lessee_ctx.to_policy_values(),
                                       lessee_ctx.to_policy_values()),
            None]

        utils.contract_authorize_management(
            test_contract, owner_ctx.to_policy_values()
        )

        mock_authorize.assert_called_once_with(
            'esi_leap:contract:contract_admin',
            owner_ctx.to_policy_values(),
            owner_ctx.to_policy_values())

        mock_get.assert_called_with(test_contract.offer_uuid)

    @mock.patch('esi_leap.api.controllers.v1.utils.offer.Offer.get')
    @mock.patch('esi_leap.api.controllers.v1.utils.policy.authorize')
    def test__contract_authorize_management_invalid_owner(self,
                                                          mock_authorize,
                                                          mock_get):
        mock_get.return_value = test_offer
        mock_authorize.side_effect = [
            policy.PolicyNotAuthorized('esi_leap:contract:contract_admin',
                                       owner_ctx_2.to_policy_values(),
                                       owner_ctx_2.to_policy_values()),
            policy.PolicyNotAuthorized('esi_leap:offer:offer_admin',
                                       owner_ctx_2.to_policy_values(),
                                       owner_ctx_2.to_policy_values())
        ]

        self.assertRaises(policy.PolicyNotAuthorized,
                          utils.contract_authorize_management,
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

        mock_get.assert_called_with(test_contract_3.offer_uuid)


class TestGetObjectUtils(testtools.TestCase):

    @mock.patch('esi_leap.api.controllers.v1.utils.policy.authorize')
    @mock.patch('esi_leap.api.controllers.v1.utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.api.controllers.v1.utils.offer.Offer.get')
    def test_get_offer_authorized_uuid_owner(self,
                                             mock_offer_get,
                                             mock_is_uuid_like,
                                             mock_authorize):

        mock_is_uuid_like.return_value = True
        mock_offer_get.return_value = test_offer

        res = utils.get_offer_authorized(test_offer.uuid,
                                         owner_ctx.to_policy_values())

        self.assertEqual(res, test_offer)

        mock_is_uuid_like.assert_called_once_with(test_offer.uuid)
        mock_offer_get.assert_called_once_with(test_offer.uuid)
        assert not mock_authorize.called

    @mock.patch('esi_leap.api.controllers.v1.utils.policy.authorize')
    @mock.patch('esi_leap.api.controllers.v1.utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.api.controllers.v1.utils.offer.Offer.get')
    def test_get_offer_authorized_uuid_available_owner(self,
                                                       mock_offer_get,
                                                       mock_is_uuid_like,
                                                       mock_authorize):

        mock_is_uuid_like.return_value = True
        mock_offer_get.return_value = test_offer

        res = utils.get_offer_authorized(test_offer.uuid,
                                         owner_ctx.to_policy_values(),
                                         statuses.AVAILABLE)

        self.assertEqual(res, test_offer)

        mock_is_uuid_like.assert_called_once_with(test_offer.uuid)
        mock_offer_get.assert_called_once_with(test_offer.uuid)
        assert not mock_authorize.called

    @mock.patch('esi_leap.api.controllers.v1.utils.policy.authorize')
    @mock.patch('esi_leap.api.controllers.v1.utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.api.controllers.v1.utils.offer.Offer.get')
    def test_get_offer_authorized_uuid_available_invalid_owner(
            self, mock_offer_get, mock_is_uuid_like, mock_authorize):

        mock_is_uuid_like.return_value = True
        mock_offer_get.return_value = test_offer
        mock_authorize.side_effect = [
            policy.PolicyNotAuthorized('esi_leap:offer:offer_admin',
                                       owner_ctx_2.to_policy_values(),
                                       owner_ctx_2.to_policy_values())
        ]

        self.assertRaises(exception.OfferNotFound,
                          utils.get_offer_authorized,
                          test_offer.uuid,
                          owner_ctx_2.to_policy_values(),
                          statuses.AVAILABLE)

        mock_is_uuid_like.assert_called_once_with(test_offer.uuid)
        mock_offer_get.assert_called_once_with(test_offer.uuid)
        mock_authorize.assert_called_once_with('esi_leap:offer:offer_admin',
                                               owner_ctx_2.to_policy_values(),
                                               owner_ctx_2.to_policy_values())

    @mock.patch('esi_leap.api.controllers.v1.utils.policy.authorize')
    @mock.patch('esi_leap.api.controllers.v1.utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.api.controllers.v1.utils.offer.Offer.get')
    def test_get_offer_authorized_uuid_available_admin(self,
                                                       mock_offer_get,
                                                       mock_is_uuid_like,
                                                       mock_authorize):

        mock_is_uuid_like.return_value = True
        mock_offer_get.return_value = test_offer

        utils.get_offer_authorized(test_offer.uuid,
                                   admin_ctx.to_policy_values(),
                                   statuses.AVAILABLE)

        mock_is_uuid_like.assert_called_once_with(test_offer.uuid)
        mock_offer_get.assert_called_once_with(test_offer.uuid)
        mock_authorize.assert_called_once_with('esi_leap:offer:offer_admin',
                                               admin_ctx.to_policy_values(),
                                               admin_ctx.to_policy_values())

    @mock.patch('esi_leap.api.controllers.v1.utils.policy.authorize')
    @mock.patch('esi_leap.api.controllers.v1.utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.api.controllers.v1.utils.offer.Offer.get_all')
    def test_get_offer_authorized_name_available_owner(self,
                                                       mock_offer_get_all,
                                                       mock_is_uuid_like,
                                                       mock_authorize):

        mock_is_uuid_like.return_value = False
        mock_offer_get_all.return_value = [test_offer]

        res = utils.get_offer_authorized(test_offer.name,
                                         owner_ctx.to_policy_values(),
                                         statuses.AVAILABLE)

        self.assertEqual(res, test_offer)

        mock_is_uuid_like.assert_called_once_with(test_offer.name)
        mock_offer_get_all.assert_called_once_with(
            {'name': test_offer.name,
             'status': statuses.AVAILABLE}
        )
        mock_authorize.assert_called_once()

    @mock.patch('esi_leap.api.controllers.v1.utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.api.controllers.v1.utils.offer.Offer.get')
    def test_get_offer_uuid(self, mock_offer_get, mock_is_uuid_like):

        mock_is_uuid_like.return_value = True
        mock_offer_get.return_value = test_offer

        res = utils.get_offer(test_offer.uuid)

        self.assertEqual(res, test_offer)

        mock_is_uuid_like.assert_called_once_with(test_offer.uuid)
        mock_offer_get.assert_called_once_with(test_offer.uuid)

    @mock.patch('esi_leap.api.controllers.v1.utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.api.controllers.v1.utils.offer.Offer.get')
    def test_get_offer_uuid_available(self,
                                      mock_offer_get,
                                      mock_is_uuid_like):

        mock_is_uuid_like.return_value = True
        mock_offer_get.return_value = test_offer

        res = utils.get_offer(test_offer.uuid, statuses.AVAILABLE)

        self.assertEqual(res, test_offer)

        mock_is_uuid_like.assert_called_once_with(test_offer.uuid)
        mock_offer_get.assert_called_once_with(test_offer.uuid)

    @mock.patch('esi_leap.api.controllers.v1.utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.api.controllers.v1.utils.offer.Offer.get')
    def test_get_offer_uuid_bad_status(self,
                                       mock_offer_get,
                                       mock_is_uuid_like):

        mock_is_uuid_like.return_value = True
        mock_offer_get.return_value = test_offer

        self.assertRaises(exception.OfferNotFound,
                          utils.get_offer,
                          test_offer.uuid, statuses.CANCELLED)

        mock_is_uuid_like.assert_called_once_with(test_offer.uuid)
        mock_offer_get.assert_called_once_with(test_offer.uuid)

    @mock.patch('esi_leap.api.controllers.v1.utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.api.controllers.v1.utils.offer.Offer.get_all')
    def test_get_offer_name_available(self,
                                      mock_offer_get_all,
                                      mock_is_uuid_like):

        mock_is_uuid_like.return_value = False
        mock_offer_get_all.return_value = [test_offer]

        res = utils.get_offer(test_offer.name, statuses.AVAILABLE)

        self.assertEqual(res, test_offer)

        mock_is_uuid_like.assert_called_once_with(test_offer.name)
        mock_offer_get_all.assert_called_once_with(
            {'name': test_offer.name,
             'status': statuses.AVAILABLE}
        )

    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'contract_authorize_management')
    @mock.patch('esi_leap.api.controllers.v1.utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.api.controllers.v1.utils.contract.Contract.get')
    def test_get_contract_authorized_uuid(self,
                                          mock_contract_get,
                                          mock_is_uuid_like,
                                          mock_authorize):

        mock_is_uuid_like.return_value = True
        mock_contract_get.return_value = test_contract

        res = utils.get_contract_authorized(test_contract.uuid,
                                            lessee_ctx.to_policy_values())

        self.assertEqual(res, test_contract)

        mock_is_uuid_like.assert_called_once_with(test_contract.uuid)
        mock_contract_get.assert_called_once_with(test_contract.uuid)

    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'contract_authorize_management')
    @mock.patch('esi_leap.api.controllers.v1.utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.api.controllers.v1.utils.contract.Contract.get_all')
    def test_get_contract_authorized_name(self,
                                          mock_contract_get_all,
                                          mock_is_uuid_like,
                                          mock_authorize):

        mock_is_uuid_like.return_value = False
        mock_contract_get_all.return_value = [test_contract]

        res = utils.get_contract_authorized(
            test_contract.name,
            lessee_ctx.to_policy_values(),
            [statuses.CREATED, statuses.ACTIVE])

        self.assertEqual(res, test_contract)

        mock_is_uuid_like.assert_called_once_with(test_contract.name)
        mock_contract_get_all.assert_called_once_with(
            {'name': test_contract.name,
             'status': [statuses.CREATED, statuses.ACTIVE]}
        )


class TestOffersControllerStaticMethods(testtools.TestCase):

    @mock.patch.object(test_node_1, 'is_resource_admin',
                       return_value=True)
    @mock.patch('esi_leap.api.controllers.v1.utils.policy.authorize')
    @mock.patch('esi_leap.api.controllers.v1.utils.ro_factory.'
                'ResourceObjectFactory.get_resource_object',
                return_value=test_node_1)
    def test__verify_resource_permission_owner(self,
                                               mock_gro,
                                               mock_authorize,
                                               mock_is_resource_admin):

        utils.verify_resource_permission(
            owner_ctx.to_policy_values(), test_offer.to_dict())

        mock_gro.assert_called_once_with(
            test_offer.resource_type,
            test_offer.resource_uuid)
        mock_is_resource_admin.assert_called_once_with(test_offer.project_id)
        assert not mock_authorize.called

    @mock.patch.object(test_node_2, 'is_resource_admin',
                       return_value=False)
    @mock.patch('esi_leap.api.controllers.v1.utils.policy.authorize')
    @mock.patch('esi_leap.api.controllers.v1.utils.ro_factory.'
                'ResourceObjectFactory.get_resource_object',
                return_value=test_node_2)
    def test__verify_resource_permission_admin(self,
                                               mock_gro,
                                               mock_authorize,
                                               mock_is_resource_admin):

        bad_test_offer = offer.Offer(
            resource_type='test_node',
            resource_uuid=test_node_2._uuid,
            project_id=owner_ctx.project_id
        )

        utils.verify_resource_permission(admin_ctx.to_policy_values(),
                                         bad_test_offer.to_dict())

        mock_gro.assert_called_once_with(
            bad_test_offer.resource_type,
            bad_test_offer.resource_uuid)
        mock_is_resource_admin.assert_called_once_with(
            bad_test_offer.project_id)
        mock_authorize.assert_called_once_with('esi_leap:offer:offer_admin',
                                               admin_ctx.to_policy_values(),
                                               admin_ctx.to_policy_values())

    @mock.patch.object(test_node_2, 'is_resource_admin',
                       return_value=False)
    @mock.patch('esi_leap.api.controllers.v1.utils.policy.authorize')
    @mock.patch('esi_leap.api.controllers.v1.utils.ro_factory.'
                'ResourceObjectFactory.get_resource_object',
                return_value=test_node_2)
    def test__verify_resource_permission_invalid_owner(self,
                                                       mock_gro,
                                                       mock_authorize,
                                                       mock_is_resource_admin):

        mock_authorize.side_effect = policy.PolicyNotAuthorized(
            'esi_leap:offer:offer_admin',
            owner_ctx.to_dict(), owner_ctx.to_dict())

        bad_test_offer = offer.Offer(
            resource_type='test_node',
            resource_uuid=test_node_2._uuid,
            project_id=owner_ctx.project_id
        )

        self.assertRaises(policy.PolicyNotAuthorized,
                          utils.verify_resource_permission,
                          owner_ctx_2.to_policy_values(),
                          bad_test_offer.to_dict())

        mock_gro.assert_called_once_with(
            bad_test_offer.resource_type,
            bad_test_offer.resource_uuid)
        mock_is_resource_admin.assert_called_once_with(
            bad_test_offer.project_id)
        mock_authorize.assert_called_once_with('esi_leap:offer:offer_admin',
                                               owner_ctx_2.to_policy_values(),
                                               owner_ctx_2.to_policy_values())
