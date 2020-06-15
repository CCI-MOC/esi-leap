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

from esi_leap.api.controllers import types as types
import unittest as unittest


class TestCollection(unittest.TestCase):

    def setUp(self):
        self.test_collection = types.Collection()
        self.test_collection._type = 'stuff'
        self.test_collection.stuff = [1, 2, 3]

    def test_has_next(self):
        self.assertEqual(self.test_collection.has_next(3), True)
        self.assertEqual(self.test_collection.has_next(0), False)
