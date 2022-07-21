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
from esi_leap.common.exception import ResourceTypeUnknown
from esi_leap.resource_objects import base
# types derived from base won't show as subclasses unless imported somewhere
from esi_leap.resource_objects import dummy_node  # noqa: F401
from esi_leap.resource_objects import ironic_node  # noqa: F401
from esi_leap.resource_objects import test_node  # noqa: F401


_RESOURCE_TYPE_MAP = {
    typ.resource_type: typ for typ in
    base.ResourceObjectInterface.__subclasses__()}
RESOURCE_TYPES = tuple(_RESOURCE_TYPE_MAP.keys())


def get_type(resource_type):
    if resource_type in RESOURCE_TYPES:
        return _RESOURCE_TYPE_MAP[resource_type]
    else:
        raise ResourceTypeUnknown(resource_type=resource_type)


def get_resource_object(resource_type, resource_ident):
    return get_type(resource_type)(resource_ident)
