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

import mock

from esi_leap.objects import policy
from esi_leap.tests import base


def get_test_policy():
    return {
        'id': 7,
        'uuid': 'b0f45e74-fa2f-4481-bbqc-eeb59eb9e76f',
        'project_id': '01d4e6a72f5c408813e02f664cc8c83e',
        'name': 'test-policy',
        'max_time_for_lease': 86400,
        'extendible': False,
        'created_at': None,
        'updated_at': None
    }


class TestPolicyObject(base.DBTestCase):

    def setUp(self):
        super(TestPolicyObject, self).setUp()
        self.fake_policy = get_test_policy()

    def test_get(self):
        policy_uuid = self.fake_policy['uuid']
        with mock.patch.object(self.db_api, 'policy_get',
                               autospec=True) as mock_policy_get:
            mock_policy_get.return_value = self.fake_policy

            p = policy.Policy.get(self.context, policy_uuid)

            mock_policy_get.assert_called_once_with(self.context, policy_uuid)
            self.assertEqual(self.context, p._context)
