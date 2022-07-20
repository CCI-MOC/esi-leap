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

import importlib
import os
import os.path

from esi_leap.common.exception import ResourceTypeUnknown


# import all resource objects in current directory
def __get_modules():
    for module_file in os.listdir(__path__[0]):
        if module_file[0] not in ('_', '.'):
            yield __name__ + '.' + os.path.splitext(module_file)[0]


for mod_name in __get_modules():
    importlib.import_module(mod_name)

# map name of resource type to corresponding object type
_RESOURCE_TYPE_MAP = {
    typ.resource_type: typ for typ in
    base.ResourceObjectInterface.__subclasses__()}  # noqa: F821
RESOURCE_TYPES = tuple(_RESOURCE_TYPE_MAP.keys())


# module-level helper functions
def get_class(resource_type):
    if resource_type in RESOURCE_TYPES:
        return _RESOURCE_TYPE_MAP[resource_type]
    else:
        raise ResourceTypeUnknown(resource_type=resource_type)


def get_resource_object(resource_type, resource_ident):
    return get_class(resource_type)(resource_ident)
