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

from esi_leap.objects import leasable_resource
from esi_leap.tests import base


def get_test_leasable_resource():
    return {
        'id': 27,
        'resource_type': 'ironic_node',
        'resource_uuid': '8010c964-9637-4ea0-b492-9c99b07ea1db',
        'expiration_date': None,
        'request_uuid': None,
        'lease_expiration_date': None,
        'created_at': None,
        'updated_at': None
    }


class TestLeasableResourceObject(base.DBTestCase):

    def setUp(self):
        super(TestLeasableResourceObject, self).setUp()
        self.fake_leasable_resource = get_test_leasable_resource()

    def test_get(self):
        leasable_resource_type = self.fake_leasable_resource['resource_type']
        leasable_resource_uuid = self.fake_leasable_resource['resource_uuid']
        with mock.patch.object(self.db_api, 'leasable_resource_get',
                               autospec=True) as mock_resource_get:
            mock_resource_get.return_value = self.fake_leasable_resource

            r = leasable_resource.LeasableResource.get(
                self.context, leasable_resource_type, leasable_resource_uuid)

            mock_resource_get.assert_called_once_with(
                self.context, leasable_resource_type, leasable_resource_uuid)
            self.assertEqual(self.context, r._context)

    def test_get_all(self):
        with mock.patch.object(
                self.db_api, 'leasable_resource_get_all', autospec=True
        ) as mock_resource_get_all:
            mock_resource_get_all.return_value = [
                self.fake_leasable_resource]

            resources = leasable_resource.LeasableResource.get_all(
                self.context)

            mock_resource_get_all.assert_called_once_with(
                self.context)
            self.assertEqual(len(resources), 1)
            self.assertIsInstance(
                resources[0], leasable_resource.LeasableResource)
            self.assertEqual(self.context, resources[0]._context)

    def test_create(self):
        r = leasable_resource.LeasableResource(
            self.context, **self.fake_leasable_resource)
        with mock.patch.object(self.db_api, 'leasable_resource_create',
                               autospec=True) as mock_resource_create:
            mock_resource_create.return_value = get_test_leasable_resource()

            r.create(self.context)

            mock_resource_create.assert_called_once_with(
                self.context, get_test_leasable_resource())
