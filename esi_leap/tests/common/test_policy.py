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

from oslo_policy import policy as oslo_policy

from esi_leap.common import policy
import esi_leap.conf
from esi_leap.tests import base


CONF = esi_leap.conf.CONF


class PolicyTestCase(base.TestCase):

    def setUp(self):
        super(PolicyTestCase, self).setUp()

        CONF.set_override('auth_enable', True,
                          group='pecan')

    def test_authorized(self):
        creds = {'roles': ['esi_leap_owner']}
        self.assertTrue(policy.authorize('esi_leap:offer:get',
                                         creds, creds))

    def test_unauthorized(self):
        creds = {'roles': ['generic_user']}
        self.assertRaises(
            oslo_policy.PolicyNotAuthorized,
            policy.authorize, 'esi_leap:offer:get', creds, creds)

    def test_authorize_policy_not_registered(self):
        creds = {'roles': ['generic_user']}
        self.assertRaises(
            oslo_policy.PolicyNotRegistered,
            policy.authorize, 'esi_leap:foo:bar', creds, creds)
