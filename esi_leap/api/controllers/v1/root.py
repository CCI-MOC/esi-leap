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

from oslo_serialization import jsonutils
import pecan
from pecan import rest

from esi_leap.api.controllers.v1 import event
from esi_leap.api.controllers.v1 import lease
from esi_leap.api.controllers.v1 import node
from esi_leap.api.controllers.v1 import offer


class Controller(rest.RestController):

    leases = lease.LeasesController()
    offers = offer.OffersController()
    nodes = node.NodesController()
    events = event.EventsController()

    @pecan.expose(content_type='application/json')
    def index(self):
        pecan.response.status_code = 300
        pecan.response.content_type = 'application/json'
        versions = {
            'versions': [
                {
                    'id': 'v1.0',
                    'status': 'CURRENT',
                    'links': [{
                        'href': '{0}/v1'.format(pecan.request.host_url),
                        'rel': 'self'
                    }]
                }
            ]
        }
        return jsonutils.dump_as_bytes(versions)
