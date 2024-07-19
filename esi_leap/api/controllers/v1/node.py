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

import concurrent.futures
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
    maintenance = wsme.wsattr(wtypes.text)
    provision_state = wsme.wsattr(wtypes.text)
    target_provision_state = wsme.wsattr(wtypes.text)
    power_state = wsme.wsattr(wtypes.text)
    target_power_state = wsme.wsattr(wtypes.text)
    properties = {wtypes.text: types.jsontype}
    resource_class = wsme.wsattr(wtypes.text)
    uuid = wsme.wsattr(wtypes.text)
    offer_uuid = wsme.wsattr(wtypes.text)
    lease_uuid = wsme.wsattr(wtypes.text)
    lessee = wsme.wsattr(wtypes.text)
    future_offers = wsme.wsattr([wtypes.text])
    future_leases = wsme.wsattr([wtypes.text])

    def __init__(self, **kwargs):
        self.fields = (
            "name",
            "owner",
            "uuid",
            "offer_uuid",
            "lease_uuid",
            "lessee",
            "future_offers",
            "future_leases",
            "resource_class",
            "provision_state",
            "maintenance",
            "properties",
            "target_provision_state",
            "power_state",
            "target_power_state",
        )
        for field in self.fields:
            setattr(self, field, kwargs.get(field, wtypes.Unset))


class NodeCollection(types.Collection):
    nodes = [Node]

    def __init__(self, **kwargs):
        self._type = "nodes"
        self.nodes = kwargs.get("nodes", [])


class NodesController(rest.RestController):
    @wsme_pecan.wsexpose(NodeCollection, wtypes.text, wtypes.text, wtypes.text)
    def get_all(self, resource_class=None, owner=None, lessee=None):
        context = pecan.request.context

        if owner is not None:
            owner = keystone.get_project_uuid_from_ident(owner)
        if lessee is not None:
            lessee = keystone.get_project_uuid_from_ident(lessee)

        filter_args = {
            "resource_class": resource_class,
            "owner": owner,
            "lessee": lessee,
        }

        nodes = None
        project_list = None

        with concurrent.futures.ThreadPoolExecutor() as executor:
            filter_args = {k: v for k, v in filter_args.items() if v is not None}
            f1 = executor.submit(ironic.get_node_list, context, **filter_args)
            f2 = executor.submit(keystone.get_project_list)
            nodes = f1.result()
            project_list = f2.result()

        node_collection = NodeCollection()

        now = datetime.now()

        offers = offer_obj.Offer.get_all({"status": [statuses.AVAILABLE]}, context)

        leases = lease_obj.Lease.get_all({"status": [statuses.CREATED]}, context)

        for node in nodes:
            f_offer_uuids = []
            current_offer = None

            node_offers = [
                offer for offer in offers if offer.resource_uuid == node.uuid
            ]

            for offer in node_offers:
                if offer.start_time > now:
                    f_offer_uuids.append(offer.uuid)
                elif offer.end_time >= now:
                    current_offer = offer

            f_lease_uuids = [
                lease.uuid for lease in leases if lease.resource_uuid == node.uuid
            ]

            n = Node(
                name=node.name,
                uuid=node.uuid,
                provision_state=node.provision_state,
                target_provision_state=node.target_provision_state,
                power_state=node.power_state,
                target_power_state=node.target_power_state,
                resource_class=node.resource_class,
                properties=ironic.get_condensed_properties(node.properties),
                maintenance=str(node.maintenance),
                owner=keystone.get_project_name(node.owner, project_list),
                lessee=keystone.get_project_name(node.lessee, project_list),
                future_offers=f_offer_uuids,
                future_leases=f_lease_uuids,
            )

            if current_offer:
                n.offer_uuid = current_offer.uuid
            if "lease_uuid" in node.properties:
                n.lease_uuid = node.properties["lease_uuid"]

            node_collection.nodes.append(n)

        return node_collection
