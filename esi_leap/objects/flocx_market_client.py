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
# borrowed from Nova
import esi_leap.conf
from oslo_log import log as logging

LOG = logging.getLogger(__name__)
CONF = esi_leap.conf.CONF


class FlocxMarketClient(object):
    """Client class for flocx-market."""

    def __init__(self, adapter=None):
        self._adapter = adapter
        self._client = self._create_client()

    def _create_client(self):
        """Create the HTTP session accessing the flocx-market service."""
        client = self._adapter
        client.additional_headers = {'accept': 'application/json'}
        return client

    def get(self, url, version=None, global_request_id=None):
        headers = ({request_id.INBOUND_HEADER: global_request_id}
                   if global_request_id else {})
        return self._client.get(url, microversion=version, headers=headers)

    def post(self, url, data, version=None, global_request_id=None):
        headers = ({request_id.INBOUND_HEADER: global_request_id}
                   if global_request_id else {})
        return self._client.post(url, json=data, microversion=version,
                                 headers=headers)

    def put(self, url, data, version=None, global_request_id=None):
        kwargs = {'microversion': version,
                  'headers': {request_id.INBOUND_HEADER:
                              global_request_id} if global_request_id else {}}
        if data is not None:
            kwargs['json'] = data
        return self._client.put(url, **kwargs)

    def delete(self, url, version=None, global_request_id=None):
        headers = ({request_id.INBOUND_HEADER: global_request_id}
                   if global_request_id else {})
        return self._client.delete(url, microversion=version, headers=headers)

    def send_offer(self, data):
        url = CONF.flocx_market.endpoint_override + '/offer'
        r = self.post(url, data)
        if r.status_code != 201:
            LOG.warning(
                "Failed to send an offer to flocx-market. Got HTTP %s: %s",
                r.status_code,
                r.text)
        return r.status_code
