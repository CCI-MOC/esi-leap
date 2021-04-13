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
from oslo_policy import policy as oslo_policy
from oslo_utils import uuidutils

import testtools

from esi_leap.api.controllers.v1 import utils
from esi_leap.common import exception
from esi_leap.common import policy
from esi_leap.common import statuses
from esi_leap.objects import lease
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

test_lease = lease.Lease(
    offer_uuid=o_uuid,
    name='c',
    uuid=uuidutils.generate_uuid(),
    project_id=lessee_ctx.project_id,
    owner_id=owner_ctx.project_id,
    status=statuses.CREATED
)

test_lease_2 = lease.Lease(
    offer_uuid=o_uuid,
    name='c',
    uuid=uuidutils.generate_uuid(),
    project_id=lessee_ctx.project_id,
    owner_id=owner_ctx.project_id,
    status=statuses.CREATED
)

test_lease_3 = lease.Lease(
    offer_uuid=o_uuid,
    name='c',
    uuid=uuidutils.generate_uuid(),
    project_id=lessee_ctx_2.project_id,
    owner_id=owner_ctx.project_id,
    status=statuses.CREATED
)

test_lease_4 = lease.Lease(
    offer_uuid=o_uuid,
    name='c2',
    uuid=uuidutils.generate_uuid(),
    project_id=lessee_ctx_2.project_id,
    owner_id=owner_ctx.project_id,
    status=statuses.CREATED
)


class TestManagementUtils(testtools.TestCase):

    @mock.patch('esi_leap.objects.offer.Offer.get')
    @mock.patch.object(policy, 'authorize', spec=True)
    def test_lease_authorize_management_valid_lessee(self,
                                                     mock_authorize,
                                                     mock_get):
        utils.lease_authorize_management(
            test_lease, lessee_ctx.to_policy_values()
        )

        assert not mock_authorize.called
        assert not mock_get.called

    @mock.patch('esi_leap.objects.offer.Offer.get')
    @mock.patch.object(policy, 'authorize', spec=True)
    def test_lease_authorize_management_invalid_lessee(self,
                                                       mock_authorize,
                                                       mock_get):
        mock_get.return_value = test_offer
        mock_authorize.side_effect = [
            oslo_policy.PolicyNotAuthorized('esi_leap:lease:lease_admin',
                                            lessee_ctx.to_policy_values(),
                                            lessee_ctx.to_policy_values()),
            oslo_policy.PolicyNotAuthorized('esi_leap:offer:offer_admin',
                                            lessee_ctx.to_policy_values(),
                                            lessee_ctx.to_policy_values())
        ]

        self.assertRaises(oslo_policy.PolicyNotAuthorized,
                          utils.lease_authorize_management,
                          test_lease_3, lessee_ctx.to_policy_values())

        mock_authorize.assert_has_calls(
            [
                mock.call('esi_leap:lease:lease_admin',
                          lessee_ctx.to_policy_values(),
                          lessee_ctx.to_policy_values()),
                mock.call('esi_leap:offer:offer_admin',
                          lessee_ctx.to_policy_values(),
                          lessee_ctx.to_policy_values())
            ])

        mock_get.assert_called_with(test_lease_3.offer_uuid)

    @mock.patch('esi_leap.objects.offer.Offer.get')
    @mock.patch.object(policy, 'authorize', spec=True)
    def test_lease_authorize_management_valid_owner(self,
                                                    mock_authorize,
                                                    mock_get):
        mock_get.return_value = test_offer
        mock_authorize.side_effect = [
            oslo_policy.PolicyNotAuthorized('esi_leap:lease:lease_admin',
                                            lessee_ctx.to_policy_values(),
                                            lessee_ctx.to_policy_values()),
            None]

        utils.lease_authorize_management(
            test_lease, owner_ctx.to_policy_values()
        )

        assert not mock_authorize.called
        assert not mock_get.called

    @mock.patch('esi_leap.objects.offer.Offer.get')
    @mock.patch.object(policy, 'authorize', spec=True)
    def test_lease_authorize_management_invalid_owner(self,
                                                      mock_authorize,
                                                      mock_get):
        mock_get.return_value = test_offer
        mock_authorize.side_effect = [
            oslo_policy.PolicyNotAuthorized('esi_leap:lease:lease_admin',
                                            owner_ctx_2.to_policy_values(),
                                            owner_ctx_2.to_policy_values()),
            oslo_policy.PolicyNotAuthorized('esi_leap:offer:offer_admin',
                                            owner_ctx_2.to_policy_values(),
                                            owner_ctx_2.to_policy_values())
        ]

        self.assertRaises(oslo_policy.PolicyNotAuthorized,
                          utils.lease_authorize_management,
                          test_lease_3, owner_ctx_2.to_policy_values())

        mock_authorize.assert_has_calls(
            [
                mock.call('esi_leap:lease:lease_admin',
                          owner_ctx_2.to_policy_values(),
                          owner_ctx_2.to_policy_values()),
                mock.call('esi_leap:offer:offer_admin',
                          owner_ctx_2.to_policy_values(),
                          owner_ctx_2.to_policy_values())
            ])

        mock_get.assert_called_with(test_lease_3.offer_uuid)


class TestGetObjectUtils(testtools.TestCase):

    @mock.patch.object(policy, 'authorize', spec=True)
    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.offer.Offer.get')
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

    @mock.patch.object(policy, 'authorize', spec=True)
    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.offer.Offer.get')
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

    @mock.patch.object(policy, 'authorize', spec=True)
    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.offer.Offer.get')
    def test_get_offer_authorized_uuid_available_invalid_owner(
            self, mock_offer_get, mock_is_uuid_like, mock_authorize):

        mock_is_uuid_like.return_value = True
        mock_offer_get.return_value = test_offer
        mock_authorize.side_effect = [
            oslo_policy.PolicyNotAuthorized('esi_leap:offer:offer_admin',
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

    @mock.patch.object(policy, 'authorize', spec=True)
    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.offer.Offer.get')
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

    @mock.patch.object(policy, 'authorize', spec=True)
    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.offer.Offer.get_all')
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

    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.offer.Offer.get')
    def test_get_offer_uuid(self, mock_offer_get, mock_is_uuid_like):

        mock_is_uuid_like.return_value = True
        mock_offer_get.return_value = test_offer

        res = utils.get_offer(test_offer.uuid)

        self.assertEqual(res, test_offer)

        mock_is_uuid_like.assert_called_once_with(test_offer.uuid)
        mock_offer_get.assert_called_once_with(test_offer.uuid)

    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.offer.Offer.get')
    def test_get_offer_uuid_available(self,
                                      mock_offer_get,
                                      mock_is_uuid_like):

        mock_is_uuid_like.return_value = True
        mock_offer_get.return_value = test_offer

        res = utils.get_offer(test_offer.uuid, statuses.AVAILABLE)

        self.assertEqual(res, test_offer)

        mock_is_uuid_like.assert_called_once_with(test_offer.uuid)
        mock_offer_get.assert_called_once_with(test_offer.uuid)

    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.offer.Offer.get')
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

    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.offer.Offer.get_all')
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
                'lease_authorize_management')
    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.lease.Lease.get')
    def test_get_lease_authorized_uuid(self,
                                       mock_lease_get,
                                       mock_is_uuid_like,
                                       mock_authorize):

        mock_is_uuid_like.return_value = True
        mock_lease_get.return_value = test_lease

        res = utils.get_lease_authorized(test_lease.uuid,
                                         lessee_ctx.to_policy_values())

        self.assertEqual(res, test_lease)

        mock_is_uuid_like.assert_called_once_with(test_lease.uuid)
        mock_lease_get.assert_called_once_with(test_lease.uuid)

    @mock.patch('esi_leap.api.controllers.v1.utils.'
                'lease_authorize_management')
    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.lease.Lease.get_all')
    def test_get_lease_authorized_name(self,
                                       mock_lease_get_all,
                                       mock_is_uuid_like,
                                       mock_authorize):

        mock_is_uuid_like.return_value = False
        mock_lease_get_all.return_value = [test_lease]

        res = utils.get_lease_authorized(
            test_lease.name,
            lessee_ctx.to_policy_values(),
            [statuses.CREATED, statuses.ACTIVE])

        self.assertEqual(res, test_lease)

        mock_is_uuid_like.assert_called_once_with(test_lease.name)
        mock_lease_get_all.assert_called_once_with(
            {'name': test_lease.name,
             'status': [statuses.CREATED, statuses.ACTIVE]}
        )


class TestOffersControllerStaticMethods(testtools.TestCase):

    @mock.patch.object(test_node_1, 'is_resource_admin',
                       return_value=True)
    @mock.patch.object(policy, 'authorize', spec=True)
    @mock.patch('esi_leap.api.controllers.v1.utils.ro_factory.'
                'ResourceObjectFactory.get_resource_object',
                return_value=test_node_1)
    def test_verify_resource_permission_owner(self,
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
    @mock.patch.object(policy, 'authorize', spec=True)
    @mock.patch('esi_leap.api.controllers.v1.utils.ro_factory.'
                'ResourceObjectFactory.get_resource_object',
                return_value=test_node_2)
    def test_verify_resource_permission_admin(self,
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
    @mock.patch.object(policy, 'authorize', spec=True)
    @mock.patch('esi_leap.api.controllers.v1.utils.ro_factory.'
                'ResourceObjectFactory.get_resource_object',
                return_value=test_node_2)
    def test_verify_resource_permission_invalid_owner(self,
                                                      mock_gro,
                                                      mock_authorize,
                                                      mock_is_resource_admin):

        mock_authorize.side_effect = oslo_policy.PolicyNotAuthorized(
            'esi_leap:offer:offer_admin',
            owner_ctx.to_dict(), owner_ctx.to_dict())

        bad_test_offer = offer.Offer(
            resource_type='test_node',
            resource_uuid=test_node_2._uuid,
            project_id=owner_ctx.project_id
        )

        self.assertRaises(oslo_policy.PolicyNotAuthorized,
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
