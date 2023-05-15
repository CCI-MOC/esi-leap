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


admin_ctx = ctx.RequestContext(project_id='adminid', roles=['admin'])

owner_ctx = ctx.RequestContext(project_id='ownerid', roles=['owner'])
owner_ctx_dict = owner_ctx.to_policy_values()

lessee_ctx = ctx.RequestContext(project_id='lesseeid', roles=['lessee'])
lessee_ctx_dict = lessee_ctx.to_policy_values()

owner_ctx_2 = ctx.RequestContext(project_id='ownerid2', roles=['owner'])
lessee_ctx_2 = ctx.RequestContext(project_id='lesseeid2', roles=['lessee'])


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
    name='o',
    uuid=o_uuid,
    lessee_id=None,
    status=statuses.AVAILABLE,
    start_time=start,
    end_time=end,
    project_id=owner_ctx.project_id
)

test_offer_2 = offer.Offer(
    resource_type='test_node',
    resource_uuid=test_node_1._uuid,
    name='o',
    uuid=uuidutils.generate_uuid(),
    lessee_id=None,
    status=statuses.EXPIRED,
    start_time=start,
    end_time=end,
    project_id=owner_ctx.project_id
)

test_offer_lessee_match = offer.Offer(
    resource_type='test_node',
    resource_uuid=test_node_1._uuid,
    name='o',
    uuid=uuidutils.generate_uuid(),
    lessee_id='lesseeid',
    status=statuses.EXPIRED,
    start_time=start,
    end_time=end,
    project_id=owner_ctx.project_id
)

test_offer_lessee_no_match = offer.Offer(
    resource_type='test_node',
    resource_uuid=test_node_1._uuid,
    name='o',
    uuid=uuidutils.generate_uuid(),
    lessee_id='otherlesseeid',
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


class TestGetObjectUtils(testtools.TestCase):

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
    def test_get_offer_uuid_available(self, mock_offer_get, mock_is_uuid_like):

        mock_is_uuid_like.return_value = True
        mock_offer_get.return_value = test_offer

        res = utils.get_offer(test_offer.uuid, statuses.AVAILABLE)

        self.assertEqual(res, test_offer)

        mock_is_uuid_like.assert_called_once_with(test_offer.uuid)
        mock_offer_get.assert_called_once_with(test_offer.uuid)

    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.offer.Offer.get')
    def test_get_offer_uuid_bad_status(self, mock_offer_get,
                                       mock_is_uuid_like):

        mock_is_uuid_like.return_value = True
        mock_offer_get.return_value = test_offer

        self.assertRaises(exception.OfferNotFound,
                          utils.get_offer,
                          test_offer.uuid, statuses.DELETED)

        mock_is_uuid_like.assert_called_once_with(test_offer.uuid)
        mock_offer_get.assert_called_once_with(test_offer.uuid)

    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.offer.Offer.get_all')
    def test_get_offer_name_available(self, mock_offer_get_all,
                                      mock_is_uuid_like):

        mock_is_uuid_like.return_value = False
        mock_offer_get_all.return_value = [test_offer]

        res = utils.get_offer(test_offer.name, statuses.AVAILABLE)

        self.assertEqual(res, test_offer)

        mock_is_uuid_like.assert_called_once_with(test_offer.name)
        mock_offer_get_all.assert_called_once_with(
            {'name': test_offer.name,
             'status': statuses.AVAILABLE})

    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.lease.Lease.get')
    def test_get_lease_uuid(self, mock_lease_get, mock_is_uuid_like):

        mock_is_uuid_like.return_value = True
        mock_lease_get.return_value = test_lease

        res = utils.get_lease(test_lease.uuid)

        self.assertEqual(res, test_lease)

        mock_is_uuid_like.assert_called_once_with(test_lease.uuid)
        mock_lease_get.assert_called_once_with(test_lease.uuid)

    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.lease.Lease.get')
    def test_get_lease_uuid_available(self, mock_lease_get, mock_is_uuid_like):

        mock_is_uuid_like.return_value = True
        mock_lease_get.return_value = test_lease

        res = utils.get_lease(test_lease.uuid, [statuses.CREATED])

        self.assertEqual(res, test_lease)

        mock_is_uuid_like.assert_called_once_with(test_lease.uuid)
        mock_lease_get.assert_called_once_with(test_lease.uuid)

    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.lease.Lease.get')
    def test_get_lease_uuid_bad_status(self, mock_lease_get,
                                       mock_is_uuid_like):

        mock_is_uuid_like.return_value = True
        mock_lease_get.return_value = test_lease

        self.assertRaises(exception.LeaseNotFound,
                          utils.get_lease,
                          test_lease.uuid, statuses.DELETED)

        mock_is_uuid_like.assert_called_once_with(test_lease.uuid)
        mock_lease_get.assert_called_once_with(test_lease.uuid)

    @mock.patch('oslo_utils.uuidutils.is_uuid_like')
    @mock.patch('esi_leap.objects.lease.Lease.get_all')
    def test_get_lease_name_active(self, mock_lease_get_all,
                                   mock_is_uuid_like):

        mock_is_uuid_like.return_value = False
        mock_lease_get_all.return_value = [test_lease]

        res = utils.get_lease(test_lease.name, statuses.ACTIVE)

        self.assertEqual(res, test_lease)

        mock_is_uuid_like.assert_called_once_with(test_lease.name)
        mock_lease_get_all.assert_called_once_with(
            {'name': test_lease.name,
             'status': statuses.ACTIVE})


class TestCheckResourceAdminUtils(testtools.TestCase):

    @mock.patch.object(test_node_1, 'get_owner_project_id')
    @mock.patch('esi_leap.api.controllers.v1.utils.resource_policy_authorize')
    def test_check_resource_admin_owner(self, mock_authorize, mock_gopi):
        mock_gopi.return_value = owner_ctx.project_id

        utils.check_resource_admin(owner_ctx.to_policy_values(),
                                   test_node_1,
                                   test_offer.project_id)
        mock_gopi.assert_called_once()
        mock_authorize.assert_not_called()

    @mock.patch.object(test_node_2, 'get_owner_project_id')
    @mock.patch('esi_leap.api.controllers.v1.utils.resource_policy_authorize')
    def test_check_resource_admin_admin(self, mock_authorize, mock_gopi):
        mock_gopi.return_value = owner_ctx_2.project_id

        bad_test_offer = offer.Offer(
            resource_type='test_node',
            resource_uuid=test_node_2._uuid,
            project_id=owner_ctx.project_id
        )

        utils.check_resource_admin(admin_ctx.to_policy_values(),
                                   test_node_2,
                                   bad_test_offer.project_id)

        mock_gopi.assert_called_once()
        mock_authorize.assert_called_once_with('esi_leap:offer:offer_admin',
                                               admin_ctx.to_policy_values(),
                                               admin_ctx.to_policy_values(),
                                               'test_node', test_node_2._uuid)

    @mock.patch.object(test_node_2, 'get_owner_project_id')
    @mock.patch('esi_leap.api.controllers.v1.utils.resource_policy_authorize')
    def test_check_resource_admin_invalid_owner(self, mock_authorize,
                                                mock_gopi):
        mock_gopi.return_value = owner_ctx_2.project_id
        mock_authorize.side_effect = exception.HTTPResourceForbidden(
            resource_type='test_node', resource=test_node_2._uuid)

        bad_test_offer = offer.Offer(
            resource_type='test_node',
            resource_uuid=test_node_2._uuid,
            project_id=owner_ctx.project_id
        )

        self.assertRaises(exception.HTTPResourceForbidden,
                          utils.check_resource_admin,
                          owner_ctx_2.to_policy_values(),
                          test_node_2,
                          bad_test_offer.project_id)

        mock_gopi.assert_called_once()
        mock_authorize.assert_called_once_with('esi_leap:offer:offer_admin',
                                               owner_ctx_2.to_policy_values(),
                                               owner_ctx_2.to_policy_values(),
                                               'test_node', test_node_2._uuid)


class TestCheckResourceLeaseAdminUtils(testtools.TestCase):

    def setUp(self):
        super(TestCheckResourceLeaseAdminUtils, self).setUp()

        self.test_lease = lease.Lease(
            uuid=uuidutils.generate_uuid(),
            start_time=datetime.datetime(2016, 7, 16, 19, 20, 30),
            end_time=datetime.datetime(2016, 8, 16, 19, 20, 30),
            parent_lease_uuid=None
        )
        self.test_lease_with_parent = lease.Lease(
            uuid=uuidutils.generate_uuid(),
            start_time=datetime.datetime(2016, 7, 16, 19, 20, 30),
            end_time=datetime.datetime(2016, 8, 16, 19, 20, 30),
            parent_lease_uuid='parent-lease-uuid'
        )

    @mock.patch('esi_leap.objects.lease.Lease.get')
    @mock.patch.object(test_node_1, 'get_lease_uuid',
                       return_value='a-lease-uuid')
    @mock.patch.object(test_node_1, 'get_lessee_project_id',
                       return_value=test_offer.project_id)
    def test_check_resource_lease_admin_okay(self, mock_glpi, mock_glu,
                                             mock_lease_get):
        mock_lease_get.return_value = self.test_lease
        parent_lease_uuid = utils.check_resource_lease_admin(
            owner_ctx.to_policy_values(),
            test_node_1,
            test_offer.project_id,
            datetime.datetime(2016, 7, 16, 19, 20, 30),
            datetime.datetime(2016, 8, 16, 19, 20, 30))

        mock_glpi.assert_called_once()
        mock_glu.assert_called_once()
        mock_lease_get.assert_called_once_with('a-lease-uuid')
        self.assertEqual('a-lease-uuid', parent_lease_uuid)

    @mock.patch('esi_leap.objects.lease.Lease.get')
    @mock.patch.object(test_node_1, 'get_lease_uuid',
                       return_value='a-lease-uuid')
    @mock.patch.object(test_node_1, 'get_lessee_project_id',
                       return_value='other-lessee')
    def test_check_resource_lease_admin_not_lessee(self, mock_glpi, mock_glu,
                                                   mock_lease_get):
        mock_lease_get.return_value = self.test_lease
        parent_lease_uuid = utils.check_resource_lease_admin(
            owner_ctx.to_policy_values(),
            test_node_1,
            test_offer.project_id,
            datetime.datetime(2016, 7, 16, 19, 20, 30),
            datetime.datetime(2016, 8, 16, 19, 20, 30))

        mock_glpi.assert_called_once()
        mock_glu.assert_not_called()
        mock_lease_get.assert_not_called()
        self.assertIsNone(parent_lease_uuid)

    @mock.patch('esi_leap.objects.lease.Lease.get')
    @mock.patch.object(test_node_1, 'get_lease_uuid',
                       return_value=None)
    @mock.patch.object(test_node_1, 'get_lessee_project_id',
                       return_value=test_offer.project_id)
    def test_check_resource_lease_admin_not_lease(self,
                                                  mock_glpi,
                                                  mock_glu,
                                                  mock_lease_get):
        mock_lease_get.return_value = self.test_lease
        parent_lease_uuid = utils.check_resource_lease_admin(
            owner_ctx.to_policy_values(),
            test_node_1,
            test_offer.project_id,
            datetime.datetime(2016, 7, 16, 19, 20, 30),
            datetime.datetime(2016, 8, 16, 19, 20, 30))

        mock_glpi.assert_called_once()
        mock_glu.assert_called_once()
        mock_lease_get.assert_not_called()
        self.assertIsNone(parent_lease_uuid)

    @mock.patch('esi_leap.objects.lease.Lease.get')
    @mock.patch.object(test_node_1, 'get_lease_uuid',
                       return_value='a-lease-uuid')
    @mock.patch.object(test_node_1, 'get_lessee_project_id',
                       return_value=test_offer.project_id)
    def test_check_resource_lease_admin_parent_lease(self,
                                                     mock_glpi,
                                                     mock_glu,
                                                     mock_lease_get):
        mock_lease_get.return_value = self.test_lease_with_parent
        parent_lease_uuid = utils.check_resource_lease_admin(
            owner_ctx.to_policy_values(),
            test_node_1,
            test_offer.project_id,
            datetime.datetime(2016, 7, 16, 19, 20, 30),
            datetime.datetime(2016, 8, 16, 19, 20, 30))

        mock_glpi.assert_called_once()
        mock_glu.assert_called_once()
        mock_lease_get.assert_called_once_with('a-lease-uuid')
        self.assertIsNone(parent_lease_uuid)

    @mock.patch('esi_leap.objects.lease.Lease.get')
    @mock.patch.object(test_node_1, 'get_lease_uuid',
                       return_value='a-lease-uuid')
    @mock.patch.object(test_node_1, 'get_lessee_project_id',
                       return_value=test_offer.project_id)
    def test_check_resource_lease_admin_bad_time(self, mock_glpi, mock_glu,
                                                 mock_lease_get):
        mock_lease_get.return_value = self.test_lease
        self.assertRaises(exception.ResourceNoPermissionTime,
                          utils.check_resource_lease_admin,
                          owner_ctx.to_policy_values(),
                          test_node_1,
                          test_offer.project_id,
                          datetime.datetime(2016, 7, 15, 19, 20, 30),
                          datetime.datetime(2016, 8, 16, 19, 20, 30))
        mock_glpi.assert_called_once()
        mock_glu.assert_called_once()
        mock_lease_get.assert_called_once_with('a-lease-uuid')


class TestOfferPolicyAndRetrieveUtils(testtools.TestCase):

    @mock.patch('esi_leap.api.controllers.v1.utils.resource_policy_authorize')
    @mock.patch('esi_leap.api.controllers.v1.utils.get_offer')
    def test_check_offer_policy(self, mock_get_offer, mock_authorize):
        mock_get_offer.return_value = test_offer
        target = dict(admin_ctx.to_policy_values())
        target['offer.project_id'] = test_offer.project_id

        offer = utils.check_offer_policy_and_retrieve(
            admin_ctx, 'test_policy:test', '12345', [])

        mock_authorize.assert_called_with('test_policy:test',
                                          target,
                                          admin_ctx.to_policy_values(),
                                          'offer',
                                          test_offer.uuid)
        mock_get_offer.assert_called_with('12345', [])
        self.assertEqual(test_offer, offer)


class TestLeasePolicyAndRetrieveUtils(testtools.TestCase):

    @mock.patch('esi_leap.api.controllers.v1.utils.resource_policy_authorize')
    @mock.patch('esi_leap.api.controllers.v1.utils.get_lease')
    def test_check_lease_policy(self, mock_get_lease, mock_authorize):
        mock_get_lease.return_value = test_lease
        target = dict(admin_ctx.to_policy_values())
        target['lease.owner_id'] = test_lease.owner_id
        target['lease.project_id'] = test_lease.project_id

        lease = utils.check_lease_policy_and_retrieve(
            admin_ctx, 'test_policy:test', '12345', [])

        mock_authorize.assert_called_with('test_policy:test',
                                          target,
                                          admin_ctx.to_policy_values(),
                                          'lease',
                                          test_lease.uuid)
        mock_get_lease.assert_called_with('12345', [])
        self.assertEqual(test_lease, lease)


class TestOfferLesseeUtils(testtools.TestCase):

    @mock.patch('esi_leap.api.controllers.v1.utils.policy_authorize')
    @mock.patch('esi_leap.common.keystone.get_parent_project_id_tree')
    def test_check_offer_lessee_no_lessee_id(self,
                                             mock_gppit,
                                             mock_authorize):
        utils.check_offer_lessee(lessee_ctx.to_policy_values(),
                                 test_offer)

        assert not mock_authorize.called
        assert not mock_gppit.called

    @mock.patch.object(policy, 'authorize', spec=True)
    @mock.patch('esi_leap.common.keystone.get_parent_project_id_tree')
    def test_check_offer_lessee_owner_match(self,
                                            mock_gppit,
                                            mock_authorize):
        utils.check_offer_lessee(owner_ctx.to_policy_values(),
                                 test_offer_lessee_no_match)

        assert not mock_authorize.called
        assert not mock_gppit.called

    @mock.patch('esi_leap.api.controllers.v1.utils.policy_authorize')
    @mock.patch('esi_leap.common.keystone.get_parent_project_id_tree')
    def test_check_offer_lessee_admin(self,
                                      mock_gppit,
                                      mock_authorize):
        mock_authorize.return_value = True
        mock_gppit.return_value = [admin_ctx.project_id]

        utils.check_offer_lessee(admin_ctx.to_policy_values(),
                                 test_offer_lessee_no_match)

        mock_authorize.assert_called_once_with('esi_leap:offer:offer_admin',
                                               admin_ctx.to_policy_values(),
                                               admin_ctx.to_policy_values())
        mock_gppit.assert_called_once_with(admin_ctx.project_id)

    @mock.patch('esi_leap.api.controllers.v1.utils.policy_authorize')
    @mock.patch('esi_leap.common.keystone.get_parent_project_id_tree')
    def test_check_offer_lessee_non_admin_match(self,
                                                mock_gppit,
                                                mock_authorize):
        mock_gppit.return_value = [lessee_ctx.project_id, 'lesseeidparent']

        utils.check_offer_lessee(lessee_ctx.to_policy_values(),
                                 test_offer_lessee_match)

        assert not mock_authorize.called
        mock_gppit.assert_called_once_with(lessee_ctx.project_id)

    @mock.patch('esi_leap.api.controllers.v1.utils.policy_authorize')
    @mock.patch('esi_leap.common.keystone.get_parent_project_id_tree')
    def test_check_offer_lessee_non_admin_no_match(self,
                                                   mock_gppit,
                                                   mock_authorize):
        mock_authorize.side_effect = exception.HTTPResourceForbidden(
            resource_type='offer', resource=test_offer_lessee_no_match.uuid)
        mock_gppit.return_value = [lessee_ctx.project_id, 'lesseeidparent']

        self.assertRaises(exception.HTTPResourceForbidden,
                          utils.check_offer_lessee,
                          lessee_ctx.to_policy_values(),
                          test_offer_lessee_no_match)

        mock_authorize.assert_called_once_with('esi_leap:offer:offer_admin',
                                               lessee_ctx.to_policy_values(),
                                               lessee_ctx.to_policy_values())
        mock_gppit.assert_called_once_with(lessee_ctx.project_id)


class TestPolicyAuthorizeUtils(testtools.TestCase):

    @mock.patch.object(policy, 'authorize', spec=True)
    def test_policy_authorize(self, mock_authorize):
        utils.policy_authorize('test_policy:test',
                               lessee_ctx.to_policy_values(),
                               lessee_ctx.to_policy_values())

        mock_authorize.assert_called_once_with('test_policy:test',
                                               lessee_ctx.to_policy_values(),
                                               lessee_ctx.to_policy_values())

    @mock.patch.object(policy, 'authorize', spec=True)
    def test_policy_authorize_exception(self, mock_authorize):
        mock_authorize.side_effect = oslo_policy.PolicyNotAuthorized(
            'esi_leap:offer:offer_admin',
            lessee_ctx.to_dict(), lessee_ctx.to_dict())

        self.assertRaises(exception.HTTPForbidden,
                          utils.policy_authorize,
                          'test_policy:test',
                          lessee_ctx.to_policy_values(),
                          lessee_ctx.to_policy_values())

        mock_authorize.assert_called_once_with('test_policy:test',
                                               lessee_ctx.to_policy_values(),
                                               lessee_ctx.to_policy_values())

    @mock.patch('esi_leap.api.controllers.v1.utils.policy_authorize')
    def test_resource_policy_authorize(self, mock_authorize):
        utils.resource_policy_authorize('test_policy:test',
                                        lessee_ctx.to_policy_values(),
                                        lessee_ctx.to_policy_values(),
                                        'test_node',
                                        '12345')

        mock_authorize.assert_called_once_with('test_policy:test',
                                               lessee_ctx.to_policy_values(),
                                               lessee_ctx.to_policy_values())

    @mock.patch('esi_leap.api.controllers.v1.utils.policy_authorize')
    def test_resource_policy_authorize_exception(self, mock_authorize):
        mock_authorize.side_effect = exception.HTTPForbidden(
            'test_policy:test')

        self.assertRaises(exception.HTTPResourceForbidden,
                          utils.resource_policy_authorize,
                          'test_policy:test',
                          lessee_ctx.to_policy_values(),
                          lessee_ctx.to_policy_values(),
                          'test_node', '12345')
        mock_authorize.assert_called_once_with('test_policy:test',
                                               lessee_ctx.to_policy_values(),
                                               lessee_ctx.to_policy_values())


class TestOfferGetDictWithAddedInfoUtils(testtools.TestCase):

    @mock.patch('esi_leap.common.keystone.get_project_name')
    @mock.patch('esi_leap.objects.offer.Offer.get_availabilities')
    def test_offer_get_dict_with_added_info(self,
                                            mock_get_availabilities,
                                            mock_gpn):
        mock_get_availabilities.return_value = []
        mock_gpn.return_value = 'project-name'

        start = datetime.datetime(2016, 7, 16)
        o = offer.Offer(
            resource_type='test_node',
            resource_uuid='1234567890',
            name='o',
            status=statuses.AVAILABLE,
            start_time=start,
            end_time=start + datetime.timedelta(days=100),
            project_id=uuidutils.generate_uuid(),
            lessee_id=None
        )

        o_dict = utils.offer_get_dict_with_added_info(o)

        expected_offer_dict = {
            'resource_type': o.resource_type,
            'resource_uuid': o.resource_uuid,
            'resource_class': 'fake',
            'resource': 'test-node-1234567890',
            'name': o.name,
            'project_id': o.project_id,
            'project': 'project-name',
            'lessee_id': None,
            'lessee': 'project-name',
            'start_time': o.start_time,
            'end_time': o.end_time,
            'status': o.status,
            'availabilities': [],
        }

        self.assertEqual(expected_offer_dict, o_dict)
        self.assertEqual(2, mock_gpn.call_count)


class TestLeaseGetDictWithAddedInfoUtils(testtools.TestCase):

    def setUp(self):
        super(TestLeaseGetDictWithAddedInfoUtils, self).setUp()

        self.test_lease = lease.Lease(
            start_time=datetime.datetime(2016, 7, 16, 19, 20, 30),
            end_time=datetime.datetime(2016, 8, 16, 19, 20, 30),
            uuid=uuidutils.generate_uuid(),
            resource_type='test_node',
            resource_uuid='111',
            project_id='lesseeid',
            owner_id='ownerid',
            parent_lease_uuid=None
        )

    @mock.patch('esi_leap.resource_objects.test_node.TestNode.get_name')
    @mock.patch('esi_leap.common.keystone.get_project_name')
    @mock.patch('esi_leap.objects.lease.get_resource_object')
    def test_lease_get_dict_with_added_info(self, mock_gro, mock_gpn, mock_gn):
        mock_gro.return_value = TestNode('111')
        mock_gpn.return_value = 'project-name'
        mock_gn.return_value = 'resource-name'

        output_dict = utils.lease_get_dict_with_added_info(self.test_lease)

        expected_output_dict = self.test_lease.to_dict()
        expected_output_dict['resource'] = 'resource-name'
        expected_output_dict['project'] = 'project-name'
        expected_output_dict['owner'] = 'project-name'
        expected_output_dict['resource_class'] = 'fake'

        mock_gro.assert_called_once()
        self.assertEqual(2, mock_gpn.call_count)
        mock_gn.assert_called_once()
        self.assertEqual(expected_output_dict, output_dict)
