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

from esi_leap.common import exception
from esi_leap.resource_objects import dummy_node
from esi_leap.resource_objects import ironic_node

RESOURCE_TYPES = ['ironic_node', 'dummy_node']


class ResourceObjectFactory(object):

    @staticmethod
    def get_resource_object(resource_type, resource_uuid):
        if resource_type == 'ironic_node':
            return ironic_node.IronicNode(resource_uuid)
        elif resource_type == 'dummy_node':
            return dummy_node.DummyNode(resource_uuid)
        raise exception.ResourceTypeUnknown(resource_type=resource_type)
