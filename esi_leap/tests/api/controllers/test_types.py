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
import mock as mock
import unittest as unittest
from wsme import types as wtypes


class TestCollection(unittest.TestCase):

    def setUp(self):
        self.test_collection = types.Collection()
        self.test_collection._type = 'stuff'
        self.obj1 = mock.Mock(uuid='aaaaa')
        self.obj2 = mock.Mock(uuid='bbbbb')
        self.obj3 = mock.Mock(uuid='ccccc')
        self.test_collection.stuff = [self.obj1, self.obj2, self.obj3]
        self._type = 'url'

    def test_has_next(self):
        self.assertEqual(self.test_collection.has_next(3), True)
        self.assertEqual(self.test_collection.has_next(0), False)

    def test_get_next(self):
        kwargs = {'key1': 'Things', 'key2': 'Stuff'}
        link = ("{{'key1': 'Things', 'key2': 'Stuff'}}"
                "/v1/stuff?limit=3&marker={0}".format(self.obj3.uuid))
        self.assertEqual(self.test_collection.get_next(2, kwargs),
                         wtypes.Unset)
        self.assertEqual(self.test_collection.get_next(3, kwargs), link)
