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
from oslo_policy import policy as oslo_policy
from oslo_utils import uuidutils

from esi_leap.common import statuses
from esi_leap.objects import owner_change
from esi_leap.tests.api import base as test_api_base


TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


def _get_owner_change_response(o):
    return {
        'resource_type': o.resource_type,
        'resource_uuid': o.resource_uuid,
        'start_time': o.start_time.strftime(TIME_FORMAT),
        'end_time': o.end_time.strftime(TIME_FORMAT),
        'status': o.status,
        'uuid': o.uuid,
        'from_owner_id': o.from_owner_id,
        'to_owner_id': o.to_owner_id
    }


class TestOwnerChangesController(test_api_base.APITestCase):

    def setUp(self):
        super(TestOwnerChangesController, self).setUp()

        now = datetime.datetime(2016, 7, 16)
        self.test_oc = owner_change.OwnerChange(
            resource_type='ironic_node',
            resource_uuid=uuidutils.generate_uuid(),
            uuid=uuidutils.generate_uuid(),
            status=statuses.CREATED,
            start_time=now,
            end_time=now + datetime.timedelta(days=30),
            from_owner_id=self.context.project_id,
            to_owner_id='fake-project-id',
        )
        self.test_oc2 = owner_change.OwnerChange(
            resource_type='ironic_node',
            resource_uuid=uuidutils.generate_uuid(),
            uuid=uuidutils.generate_uuid(),
            status=statuses.CREATED,
            start_time=now,
            end_time=now + datetime.timedelta(days=30),
            from_owner_id='another-fake-project-id',
            to_owner_id='fake-project-id',
        )

    def test_empty(self):
        data = self.get_json('/owner_changes')
        self.assertEqual([], data['owner_changes'])

    def test_one(self):
        self.test_oc.create(self.context)
        data = self.get_json('/owner_changes')
        self.assertEqual(self.test_oc.uuid,
                         data['owner_changes'][0]["uuid"])

    @mock.patch('esi_leap.objects.owner_change.OwnerChange.get_all')
    @mock.patch('esi_leap.common.policy.authorize')
    def test_get_all(self, mock_authorize, mock_get_all):
        mock_get_all.return_value = [self.test_oc, self.test_oc2]

        expected_filters = {'status': [statuses.CREATED, statuses.ACTIVE]}
        expected_resp = {
            'owner_changes': [_get_owner_change_response(self.test_oc),
                              _get_owner_change_response(self.test_oc2)]}

        response = self.get_json('/owner_changes')

        assert mock_authorize.call_count == 2
        mock_authorize.assert_any_call(
            'esi_leap:owner_change:get',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_authorize.assert_any_call(
            'esi_leap:owner_change:owner_change_admin',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_get_all.assert_called_once_with(expected_filters, self.context)
        self.assertEqual(expected_resp, response)

    @mock.patch('esi_leap.objects.owner_change.OwnerChange.get_all')
    @mock.patch('esi_leap.common.policy.authorize')
    def test_get_all_any_status(self, mock_authorize, mock_get_all):
        mock_get_all.return_value = [self.test_oc, self.test_oc2]

        expected_filters = {}
        expected_resp = {
            'owner_changes': [_get_owner_change_response(self.test_oc),
                              _get_owner_change_response(self.test_oc2)]}

        response = self.get_json('/owner_changes?status=any')

        assert mock_authorize.call_count == 2
        mock_authorize.assert_any_call(
            'esi_leap:owner_change:get',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_authorize.assert_any_call(
            'esi_leap:owner_change:owner_change_admin',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_get_all.assert_called_once_with(expected_filters, self.context)
        self.assertEqual(expected_resp, response)

    @mock.patch('esi_leap.objects.owner_change.OwnerChange.get_all')
    @mock.patch('esi_leap.common.policy.authorize')
    def test_get_all_non_admin(self, mock_authorize, mock_get_all):
        mock_get_all.return_value = [self.test_oc, self.test_oc2]
        mock_authorize.side_effect = [
            None,
            oslo_policy.PolicyNotAuthorized('esi_leap:offer:offer_admin',
                                            self.context.to_policy_values(),
                                            self.context.to_policy_values())
        ]

        expected_filters = {'status': [statuses.CREATED, statuses.ACTIVE],
                            'from_or_to_owner_id': self.context.project_id}
        expected_resp = {
            'owner_changes': [_get_owner_change_response(self.test_oc),
                              _get_owner_change_response(self.test_oc2)]}

        response = self.get_json('/owner_changes')

        assert mock_authorize.call_count == 2
        mock_authorize.assert_any_call(
            'esi_leap:owner_change:get',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_authorize.assert_any_call(
            'esi_leap:owner_change:owner_change_admin',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_get_all.assert_called_once_with(expected_filters, self.context)
        self.assertEqual(expected_resp, response)

    @mock.patch('esi_leap.objects.owner_change.OwnerChange.get_all')
    @mock.patch('esi_leap.common.policy.authorize')
    def test_get_all_valid_time(self, mock_authorize, mock_get_all):
        mock_get_all.return_value = [self.test_oc, self.test_oc2]

        expected_filters = {
            'status': [statuses.CREATED, statuses.ACTIVE],
            'start_time': self.test_oc.start_time,
            'end_time': self.test_oc.end_time
        }
        expected_resp = {
            'owner_changes': [_get_owner_change_response(self.test_oc),
                              _get_owner_change_response(self.test_oc2)]}

        response = self.get_json(
            '/owner_changes?start_time=' +
            self.test_oc.start_time.strftime(TIME_FORMAT) +
            "&end_time=" +
            self.test_oc.end_time.strftime(TIME_FORMAT))

        assert mock_authorize.call_count == 2
        mock_authorize.assert_any_call(
            'esi_leap:owner_change:get',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_authorize.assert_any_call(
            'esi_leap:owner_change:owner_change_admin',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_get_all.assert_called_once_with(expected_filters, self.context)
        self.assertEqual(expected_resp, response)

    @mock.patch('esi_leap.objects.owner_change.OwnerChange.get_all')
    @mock.patch('esi_leap.common.policy.authorize')
    def test_get_all_invalid_time(self, mock_authorize, mock_get_all):
        mock_get_all.return_value = [self.test_oc, self.test_oc2]

        response = self.get_json('/owner_changes?start_time=' +
                                 self.test_oc.end_time.strftime(TIME_FORMAT) +
                                 "&end_time=" +
                                 self.test_oc.start_time.strftime(TIME_FORMAT),
                                 expect_errors=True)

        mock_authorize.assert_called_once_with(
            'esi_leap:owner_change:get',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_get_all.assert_not_called
        self.assertEqual(http_client.INTERNAL_SERVER_ERROR,
                         response.status_int)

    @mock.patch('esi_leap.objects.owner_change.OwnerChange.get')
    @mock.patch('esi_leap.common.policy.authorize')
    def test_get(self, mock_authorize, mock_get):
        mock_get.return_value = self.test_oc

        response = self.get_json('/owner_changes/' + self.test_oc.uuid)

        mock_authorize.assert_called_once_with(
            'esi_leap:owner_change:get',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_get.assert_called_once_with(self.test_oc.uuid)
        self.assertEqual(_get_owner_change_response(self.test_oc),
                         response)

    @mock.patch('esi_leap.objects.owner_change.OwnerChange.get')
    @mock.patch('esi_leap.common.policy.authorize')
    def test_get_not_to_or_from_owner(self, mock_authorize, mock_get):
        mock_get.return_value = self.test_oc2

        response = self.get_json('/owner_changes/' + self.test_oc2.uuid)

        assert mock_authorize.call_count == 2
        mock_authorize.assert_any_call(
            'esi_leap:owner_change:get',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_authorize.assert_any_call(
            'esi_leap:owner_change:owner_change_admin',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_get.assert_called_once_with(self.test_oc2.uuid)
        self.assertEqual(_get_owner_change_response(self.test_oc2),
                         response)

    @mock.patch('esi_leap.objects.owner_change.OwnerChange.get')
    @mock.patch('esi_leap.common.policy.authorize')
    def test_get_not_exist(self, mock_authorize, mock_get):
        mock_get.return_value = None

        response = self.get_json('/owner_changes/non-existent-uuid',
                                 expect_errors=True)

        mock_authorize.assert_called_once_with(
            'esi_leap:owner_change:get',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_get.assert_called_once_with('non-existent-uuid')
        self.assertEqual(http_client.INTERNAL_SERVER_ERROR,
                         response.status_int)

    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.objects.owner_change.OwnerChange.create')
    @mock.patch('esi_leap.common.policy.authorize')
    def test_post(self, mock_authorize, mock_create, mock_generate_uuid):
        mock_generate_uuid.return_value = self.test_oc.uuid
        mock_create.return_value = self.test_oc

        data = {
            "resource_type": self.test_oc.resource_type,
            "resource_uuid": self.test_oc.resource_uuid,
            "start_time": self.test_oc.start_time.strftime(TIME_FORMAT),
            "end_time": self.test_oc.end_time.strftime(TIME_FORMAT),
            "from_owner_id": self.test_oc.from_owner_id,
            "to_owner_id": self.test_oc.to_owner_id,
        }

        response = self.post_json('/owner_changes', data)

        data['uuid'] = self.test_oc.uuid

        mock_authorize.assert_called_once_with(
            'esi_leap:owner_change:create',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_create.assert_called_once
        self.assertEqual(data, response.json)
        self.assertEqual(http_client.CREATED, response.status_int)

    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.objects.owner_change.OwnerChange.create')
    @mock.patch('esi_leap.common.policy.authorize')
    def test_post_default_resource_type(self, mock_authorize, mock_create,
                                        mock_generate_uuid):
        mock_generate_uuid.return_value = self.test_oc.uuid
        mock_create.return_value = self.test_oc

        data = {
            "resource_uuid": self.test_oc.resource_uuid,
            "start_time": self.test_oc.start_time.strftime(TIME_FORMAT),
            "end_time": self.test_oc.end_time.strftime(TIME_FORMAT),
            "from_owner_id": self.test_oc.from_owner_id,
            "to_owner_id": self.test_oc.to_owner_id,
        }

        response = self.post_json('/owner_changes', data)

        data['uuid'] = self.test_oc.uuid
        data['resource_type'] = 'ironic_node'

        mock_authorize.assert_called_once_with(
            'esi_leap:owner_change:create',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_create.assert_called_once
        self.assertEqual(data, response.json)
        self.assertEqual(http_client.CREATED, response.status_int)

    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.objects.owner_change.OwnerChange.create')
    @mock.patch('esi_leap.common.policy.authorize')
    def test_post_invalid_time(self, mock_authorize, mock_create,
                               mock_generate_uuid):
        mock_generate_uuid.return_value = self.test_oc.uuid
        mock_create.return_value = self.test_oc

        data = {
            "resource_type": self.test_oc.resource_type,
            "resource_uuid": self.test_oc.resource_uuid,
            "start_time": self.test_oc.end_time.strftime(TIME_FORMAT),
            "end_time": self.test_oc.start_time.strftime(TIME_FORMAT),
            "from_owner_id": self.test_oc.from_owner_id,
            "to_owner_id": self.test_oc.to_owner_id,
        }

        response = self.post_json('/owner_changes', data, expect_errors=True)

        mock_authorize.assert_called_once_with(
            'esi_leap:owner_change:create',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_create.assert_not_called
        self.assertEqual(http_client.INTERNAL_SERVER_ERROR,
                         response.status_int)

    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    @mock.patch('esi_leap.objects.owner_change.OwnerChange.create')
    @mock.patch('esi_leap.common.policy.authorize')
    def test_post_same_from_and_to_owner(self, mock_authorize, mock_create,
                                         mock_generate_uuid):
        mock_generate_uuid.return_value = self.test_oc.uuid
        mock_create.return_value = self.test_oc

        data = {
            "resource_type": self.test_oc.resource_type,
            "resource_uuid": self.test_oc.resource_uuid,
            "start_time": self.test_oc.end_time.strftime(TIME_FORMAT),
            "end_time": self.test_oc.start_time.strftime(TIME_FORMAT),
            "from_owner_id": self.test_oc.from_owner_id,
            "to_owner_id": self.test_oc.from_owner_id,
        }

        response = self.post_json('/owner_changes', data, expect_errors=True)

        mock_authorize.assert_called_once_with(
            'esi_leap:owner_change:create',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_create.assert_not_called
        self.assertEqual(http_client.INTERNAL_SERVER_ERROR,
                         response.status_int)

    @mock.patch('esi_leap.objects.owner_change.OwnerChange.cancel')
    @mock.patch('esi_leap.objects.owner_change.OwnerChange.get')
    @mock.patch('esi_leap.common.policy.authorize')
    def test_delete(self, mock_authorize, mock_get, mock_cancel):
        mock_get.return_value = self.test_oc

        response = self.delete_json('/owner_changes/' + self.test_oc.uuid)

        mock_authorize.assert_called_once_with(
            'esi_leap:owner_change:delete',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_get.assert_called_once_with(self.test_oc.uuid)
        mock_cancel.assert_called_once
        self.assertEqual(http_client.OK, response.status_int)

    @mock.patch('esi_leap.objects.owner_change.OwnerChange.cancel')
    @mock.patch('esi_leap.objects.owner_change.OwnerChange.get')
    @mock.patch('esi_leap.common.policy.authorize')
    def test_delete_not_to_or_from_owner(self, mock_authorize, mock_get,
                                         mock_cancel):
        mock_get.return_value = self.test_oc2

        response = self.delete_json('/owner_changes/' + self.test_oc2.uuid)

        assert mock_authorize.call_count == 2
        mock_authorize.assert_any_call(
            'esi_leap:owner_change:delete',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_authorize.assert_any_call(
            'esi_leap:owner_change:owner_change_admin',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_get.assert_called_once_with(self.test_oc2.uuid)
        mock_cancel.assert_called_once
        self.assertEqual(http_client.OK, response.status_int)

    @mock.patch('esi_leap.objects.owner_change.OwnerChange.cancel')
    @mock.patch('esi_leap.objects.owner_change.OwnerChange.get')
    @mock.patch('esi_leap.common.policy.authorize')
    def test_delete_not_exist(self, mock_authorize, mock_get, mock_cancel):
        mock_get.return_value = None

        response = self.delete_json('/owner_changes/non-existent-uuid',
                                    expect_errors=True)

        mock_authorize.assert_called_once_with(
            'esi_leap:owner_change:delete',
            self.context.to_policy_values(),
            self.context.to_policy_values()
        )
        mock_cancel.assert_not_called
        self.assertEqual(http_client.INTERNAL_SERVER_ERROR,
                         response.status_int)
