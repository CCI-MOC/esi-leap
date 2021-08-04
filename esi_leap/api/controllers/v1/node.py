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

from datetime import datetime
import pecan
from pecan import rest
import wsme
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from esi_leap.api.controllers import base
from esi_leap.api.controllers import types
from esi_leap.common import ironic
from esi_leap.common import keystone
from esi_leap.common import statuses
import esi_leap.conf
from esi_leap.objects import lease as lease_obj
from esi_leap.objects import offer as offer_obj

CONF = esi_leap.conf.CONF


class Node(base.ESILEAPBase):

    name = wsme.wsattr(wtypes.text)
    owner = wsme.wsattr(wtypes.text)
    uuid = wsme.wsattr(wtypes.text)
    offer_uuid = wsme.wsattr(wtypes.text)
    lease_uuid = wsme.wsattr(wtypes.text)
    lessee = wsme.wsattr(wtypes.text)
    future_offers = wsme.wsattr(wtypes.text)
    future_leases = wsme.wsattr(wtypes.text)

    def __init__(self, **kwargs):
        self.fields = ["name", "owner", "uuid", "offer_uuid", "lease_uuid",
                       "lessee", "future_offers", "future_leases"]
        for field in self.fields:
            setattr(self, field, kwargs.get(field, wtypes.Unset))


class NodeCollection(types.Collection):
    nodes = [Node]

    def __init__(self, **kwargs):
        self._type = 'nodes'
        self.nodes = kwargs.get("nodes", [])


class NodesController(rest.RestController):

    @wsme_pecan.wsexpose(NodeCollection)
    def get_all(self):
        context = pecan.request.context
        nodes = ironic.get_node_list(context)

        node_collection = NodeCollection()

        project_list = keystone.get_project_list()
        now = datetime.now()
        for node in nodes:
            offers = offer_obj.Offer.get_all({"resource_uuid": node.uuid,
                                              "status": "available"},
                                             context)
            future_offers = []
            current_offer = None
            for offer in offers:
                if offer.start_time > now:
                    future_offers.append(offer.uuid)
                elif offer.end_time >= now:
                    current_offer = offer
            future_offers = ' '.join(future_offers)

            f_leases = lease_obj.Lease.get_all({"resource_uuid": node.uuid,
                                                "status": [statuses.CREATED]},
                                               context)
            f_lease_uuids = ' '.join([o.uuid for o in f_leases])

            n = Node(name=node.name, uuid=node.uuid,
                     owner=keystone.get_project_name(node.owner, project_list),
                     future_offers=future_offers,
                     future_leases=f_lease_uuids)
            if current_offer:
                n.offer_uuid = current_offer.uuid
            if "lease_uuid" in node.properties:
                n.lease_uuid = node.properties["lease_uuid"]
                n.lessee = keystone.get_project_name(node.lessee, project_list)

            node_collection.nodes.append(n)

        return node_collection
