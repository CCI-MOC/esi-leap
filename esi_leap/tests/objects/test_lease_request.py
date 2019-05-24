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

from esi_leap.objects import lease_request
from esi_leap.tests import base


def get_test_lease_request():
    return {
        'id': 17,
        'uuid': '96aa9fd3-a28d-46a6-bf1e-28a6d765d8d0',
        'project_id': '01d4e6a72f5c408813e02f664cc8c83e',
        'name': 'test-lease-request',
        'resource_properties': {
            'ironic_node': {
                'resource_uuids': ['8010c964-9637-4ea0-b492-9c99b07ea1db'],
                'resource_properties': [{"ram": 12800, "disk": 10}]
            }
        },
        'lease_time': 86400,
        'status': 'pending',
        'cancel_date': None,
        'fulfilled_date': None,
        'expiration_date': None,
        'created_at': None,
        'updated_at': None
    }


class TestLeaseRequestObject(base.DBTestCase):

    def setUp(self):
        super(TestLeaseRequestObject, self).setUp()
        self.fake_lease_request = get_test_lease_request()

    def test_get(self):
        lease_request_uuid = self.fake_lease_request['uuid']
        with mock.patch.object(self.db_api, 'lease_request_get',
                               autospec=True) as mock_lease_request_get:
            mock_lease_request_get.return_value = self.fake_lease_request

            r = lease_request.LeaseRequest.get(
                self.context, lease_request_uuid)

            mock_lease_request_get.assert_called_once_with(
                self.context, lease_request_uuid)
            self.assertEqual(self.context, r._context)

    def test_get_all(self):
        with mock.patch.object(self.db_api, 'lease_request_get_all',
                               autospec=True) as mock_lease_request_get_all:
            mock_lease_request_get_all.return_value = [self.fake_lease_request]

            requests = lease_request.LeaseRequest.get_all(self.context)

            mock_lease_request_get_all.assert_called_once_with(self.context)
            self.assertEqual(len(requests), 1)
            self.assertIsInstance(requests[0], lease_request.LeaseRequest)
            self.assertEqual(self.context, requests[0]._context)

    def test_get_all_by_project_id(self):
        project_id = self.fake_lease_request['project_id']
        with mock.patch.object(
                self.db_api,
                'lease_request_get_all_by_project_id',
                autospec=True) as mock_lease_request_get_all_by_project_id:
            mock_lease_request_get_all_by_project_id.return_value = [
                self.fake_lease_request]
            requests = lease_request.LeaseRequest.get_all_by_project_id(
                self.context, project_id)

            mock_lease_request_get_all_by_project_id.assert_called_once_with(
                self.context, project_id)
            self.assertEqual(len(requests), 1)
            self.assertIsInstance(requests[0], lease_request.LeaseRequest)
            self.assertEqual(self.context, requests[0]._context)

    def test_get_all_by_status(self):
        status = self.fake_lease_request['status']
        with mock.patch.object(
                self.db_api,
                'lease_request_get_all_by_status',
                autospec=True) as mock_lease_request_get_all_by_status:
            mock_lease_request_get_all_by_status.return_value = [
                self.fake_lease_request]
            requests = lease_request.LeaseRequest.get_all_by_status(
                self.context, status)

            mock_lease_request_get_all_by_status.assert_called_once_with(
                self.context, status)
            self.assertEqual(len(requests), 1)
            self.assertIsInstance(requests[0], lease_request.LeaseRequest)
            self.assertEqual(self.context, requests[0]._context)

    def test_create(self):
        r = lease_request.LeaseRequest(self.context, **self.fake_lease_request)
        with mock.patch.object(self.db_api, 'lease_request_create',
                               autospec=True) as mock_lease_request_create:
            mock_lease_request_create.return_value = get_test_lease_request()

            r.create(self.context)

            mock_lease_request_create.assert_called_once_with(
                self.context, get_test_lease_request())

    def test_destroy(self):
        r = lease_request.LeaseRequest(self.context, **self.fake_lease_request)
        with mock.patch.object(self.db_api, 'lease_request_destroy',
                               autospec=True) as mock_lease_request_destroy:

            r.destroy(self.context)

            mock_lease_request_destroy.assert_called_once_with(
                self.context, r.uuid)

    def test_save(self):
        r = lease_request.LeaseRequest(self.context, **self.fake_lease_request)
        new_name = "test-lease-request-update"
        updated_at = datetime.datetime(2006, 12, 11, 0, 0)
        with mock.patch.object(self.db_api, 'lease_request_update',
                               autospec=True) as mock_lease_request_update:
            updated_lease_request = get_test_lease_request()
            updated_lease_request['name'] = new_name
            updated_lease_request['updated_at'] = updated_at
            mock_lease_request_update.return_value = updated_lease_request

            r.name = new_name
            r.save(self.context)

            updated_values = get_test_lease_request()
            updated_values['name'] = new_name
            mock_lease_request_update.assert_called_once_with(
                self.context, r.uuid, updated_values)
            self.assertEqual(self.context, r._context)
            self.assertEqual(updated_at, r.updated_at)

    def test_expire_or_cancel(self):
        r = lease_request.LeaseRequest(self.context, **self.fake_lease_request)
        with mock.patch.object(
                self.db_api, 'leasable_resource_get_all_by_request_uuid',
                autospec=True
        ) as mock_leasable_resource_get_all_by_request_uuid:
            mock_leasable_resource_get_all_by_request_uuid.return_value = []
            with mock.patch.object(self.db_api, 'lease_request_update',
                                   autospec=True) as mock_lease_request_update:
                updated_lease_request = get_test_lease_request()
                updated_lease_request['status'] = 'expired'
                mock_lease_request_update.return_value = updated_lease_request

                r.expire_or_cancel(self.context)

                updated_values = get_test_lease_request()
                updated_values['status'] = 'expired'
                mock_lease_request_update.assert_called_once_with(
                    self.context, r.uuid, updated_values)
                self.assertEqual(self.context, r._context)
                self.assertEqual('expired', r.status)
