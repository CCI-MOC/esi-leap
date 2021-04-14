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

from esi_leap.common import utils
from esi_leap.tests import base


class LockTestCase(base.TestCase):

    def test_get_resource_lock_name(self):
        resource_type = 'ironic_node'
        resource_uuid = '12345'

        self.assertEqual(resource_type + '-' + resource_uuid,
                         utils.get_resource_lock_name(
                             resource_type, resource_uuid))
