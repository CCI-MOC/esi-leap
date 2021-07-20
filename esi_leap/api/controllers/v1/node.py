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

import pecan
from pecan import rest
import wsme
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from esi_leap.api.controllers import base
from esi_leap.api.controllers import types
from esi_leap.common import ironic
import esi_leap.conf

CONF = esi_leap.conf.CONF


class Node(base.ESILEAPBase):

    name = wsme.wsattr(wtypes.text)

    def __init__(self, **kwargs):
        setattr(self, "name", kwargs.get("name", "foo"))


class NodeCollection(types.Collection):
    nodes = [Node]

    def __init__(self, **kwargs):
        self._type = 'nodes'


class NodesController(rest.RestController):

    @wsme_pecan.wsexpose(NodeCollection)
    def get_all(self):
        context = pecan.request.context
        client = ironic.get_ironic_client(context)
        node_collection = NodeCollection()
        nodes = client.node.list()

        node_collection.nodes = [Node(name=n.name) for n in nodes]
        return node_collection
