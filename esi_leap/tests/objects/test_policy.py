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

    def test_get_all(self):
        with mock.patch.object(self.db_api, 'policy_get_all',
                               autospec=True) as mock_policy_get_all:
            mock_policy_get_all.return_value = [self.fake_policy]

            policies = policy.Policy.get_all(self.context)

            mock_policy_get_all.assert_called_once_with(self.context)
            self.assertEqual(len(policies), 1)
            self.assertIsInstance(policies[0], policy.Policy)
            self.assertEqual(self.context, policies[0]._context)

    def test_get_all_by_project_id(self):
        project_id = self.fake_policy['project_id']
        with mock.patch.object(
                self.db_api,
                'policy_get_all_by_project_id',
                autospec=True) as mock_policy_get_all_by_project_id:
            mock_policy_get_all_by_project_id.return_value = [self.fake_policy]
            policies = policy.Policy.get_all_by_project_id(
                self.context, project_id)

            mock_policy_get_all_by_project_id.assert_called_once_with(
                self.context, project_id)
            self.assertEqual(len(policies), 1)
            self.assertIsInstance(policies[0], policy.Policy)
            self.assertEqual(self.context, policies[0]._context)

    def test_create(self):
        p = policy.Policy(self.context, **self.fake_policy)
        with mock.patch.object(self.db_api, 'policy_create',
                               autospec=True) as mock_policy_create:
            mock_policy_create.return_value = get_test_policy()

            p.create(self.context)

            mock_policy_create.assert_called_once_with(self.context,
                                                       get_test_policy())

    def test_destroy(self):
        p = policy.Policy(self.context, **self.fake_policy)
        with mock.patch.object(self.db_api, 'policy_destroy',
                               autospec=True) as mock_policy_destroy:

            p.destroy(self.context)

            mock_policy_destroy.assert_called_once_with(
                self.context, p.uuid)

    def test_save(self):
        p = policy.Policy(self.context, **self.fake_policy)
        new_name = "test-policy-update"
        updated_at = datetime.datetime(2006, 12, 11, 0, 0)
        with mock.patch.object(self.db_api, 'policy_update',
                               autospec=True) as mock_policy_update:
            updated_policy = get_test_policy()
            updated_policy['name'] = new_name
            updated_policy['updated_at'] = updated_at
            mock_policy_update.return_value = updated_policy

            p.name = new_name
            p.save(self.context)

            updated_values = get_test_policy()
            updated_values['name'] = new_name
            mock_policy_update.assert_called_once_with(
                self.context, p.uuid, updated_values)
            self.assertEqual(self.context, p._context)
            self.assertEqual(updated_at, p.updated_at)
