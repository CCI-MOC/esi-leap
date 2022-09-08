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
    uuid = wsme.wsattr(wtypes.text)
    offer_uuid = wsme.wsattr(wtypes.text)
    lease_uuid = wsme.wsattr(wtypes.text)
    lessee = wsme.wsattr(wtypes.text)
    future_offers = wsme.wsattr(wtypes.text)
    future_leases = wsme.wsattr(wtypes.text)

    def __init__(self, **kwargs):
        self.fields = ('name', 'owner', 'uuid', 'offer_uuid', 'lease_uuid',
                       'lessee', 'future_offers', 'future_leases',
                       'provision_state', 'maintenance')
        for field in self.fields:
            setattr(self, field, kwargs.get(field, wtypes.Unset))


class NodeCollection(types.Collection):
    nodes = [Node]

    def __init__(self, **kwargs):
        self._type = 'nodes'
        self.nodes = kwargs.get('nodes', [])


class NodesController(rest.RestController):

    @wsme_pecan.wsexpose(NodeCollection)
    def get_all(self):
        context = pecan.request.context

        nodes = None
        project_list = None

        with concurrent.futures.ThreadPoolExecutor() as executor:
            f1 = executor.submit(ironic.get_node_list, context)
            f2 = executor.submit(keystone.get_project_list)
            nodes = f1.result()
            project_list = f2.result()

        node_collection = NodeCollection()

        now = datetime.now()

        offers = offer_obj.Offer.get_all({'status': [statuses.AVAILABLE]},
                                         context)

        leases = lease_obj.Lease.get_all({'status': [statuses.CREATED]},
                                         context)

        for node in nodes:
            future_offers = []
            current_offer = None

            node_offers = [offer for offer in offers
                           if offer.resource_uuid == node.uuid]

            for offer in node_offers:
                if offer.start_time > now:
                    future_offers.append(offer.uuid)
                elif offer.end_time >= now:
                    current_offer = offer
            future_offers = ' '.join(future_offers)

            f_lease_uuids = ''.join([lease.uuid for lease in leases
                                     if lease.resource_uuid == node.uuid])

            n = Node(name=node.name, uuid=node.uuid,
                     provision_state=node.provision_state,
                     maintenance=str(node.maintenance),
                     owner=keystone.get_project_name(node.owner, project_list),
                     lessee=keystone.get_project_name(node.lessee,
                                                      project_list),
                     future_offers=future_offers,
                     future_leases=f_lease_uuids)

            if current_offer:
                n.offer_uuid = current_offer.uuid
            if 'lease_uuid' in node.properties:
                n.lease_uuid = node.properties['lease_uuid']

            node_collection.nodes.append(n)

        return node_collection
