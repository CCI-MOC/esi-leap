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
from oslo_utils import uuidutils

from esi_leap.resource_objects.base import ResourceObjectInterface
from esi_leap.tests import base


def bind_abstract_methods(cls):
    # binds all undefined abstract methods to stub functions that do nothing
    def wrapper(*args, **kwargs):
        for method in cls.__abstractmethods__:
            setattr(cls, method, lambda: None)
        methods = set()
        for name, value in cls.__dict__.items():
            if getattr(value, "__isabstractmethod__", False):
                methods.add(name)
        cls.__abstractmethods__ = frozenset(methods)
        return cls(*args, **kwargs)
    return wrapper


@bind_abstract_methods
class ResourceObjectStub(ResourceObjectInterface):
    def __init__(self, uuid):
        self._uuid = uuid

    def get_uuid(self):
        return self._uuid


class TestResourceObjectInterface(base.TestCase):

    @mock.patch('esi_leap.db.sqlalchemy.api.resource_verify_availability')
    def test_verify_availability_for_offer(self, mock_rva):
        start = datetime.datetime(2016, 7, 16, 19, 20, 30)
        end = start + datetime.timedelta(days=10)
        fake_uuid = uuidutils.generate_uuid()
        test_node = ResourceObjectStub(fake_uuid)

        test_node.verify_availability(start, end)
        mock_rva.assert_called_once_with('base', fake_uuid, start, end)
