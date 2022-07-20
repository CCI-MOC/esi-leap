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
from esi_leap.resource_objects import ironic_node
from esi_leap.tests import base
import mock
from oslo_utils import uuidutils


class TestResourceObjectInterface(base.TestCase):

    def setUp(self):
        super(TestResourceObjectInterface, self).setUp()
        self.base_time = datetime.datetime(2016, 7, 16, 19, 20, 30)

    @mock.patch('esi_leap.db.sqlalchemy.api.resource_verify_availability')
    def test_verify_availability_for_offer(self, mock_rva):
        start = self.base_time
        end = self.base_time + datetime.timedelta(days=10)
        fake_uuid = uuidutils.generate_uuid()
        test_node = ironic_node.IronicNode(fake_uuid)

        test_node.verify_availability(start, end)
        mock_rva.assert_called_once_with('ironic_node', fake_uuid, start, end)
