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

import http.client as http_client
import pecan
from pecan import rest
import wsme
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from esi_leap.api.controllers import base
from esi_leap.common import exception
from esi_leap.common import ironic
import esi_leap.conf
from esi_leap.objects import console_auth_token as cat_obj

CONF = esi_leap.conf.CONF


class ConsoleAuthToken(base.ESILEAPBase):
    node_uuid = wsme.wsattr(wtypes.text, readonly=True)
    token = wsme.wsattr(wtypes.text, readonly=True)
    access_url = wsme.wsattr(wtypes.text, readonly=True)

    def __init__(self, **kwargs):
        self.fields = ("node_uuid", "token", "access_url")
        for field in self.fields:
            setattr(self, field, kwargs.get(field, wtypes.Unset))


class ConsoleAuthTokensController(rest.RestController):
    @wsme_pecan.wsexpose(
        ConsoleAuthToken, body={str: wtypes.text}, status_code=http_client.CREATED
    )
    def post(self, new_console_auth_token):
        context = pecan.request.context
        node_uuid_or_name = new_console_auth_token["node_uuid_or_name"]

        # get node
        client = ironic.get_ironic_client(context)
        node = client.node.get(node_uuid_or_name)
        if node is None:
            raise exception.NodeNotFound(
                uuid=node_uuid_or_name,
                resource_type="ironic_node",
                err="Node not found",
            )

        # create and authorize auth token
        cat = cat_obj.ConsoleAuthToken(node_uuid=node.uuid)
        token = cat.authorize(CONF.serialconsoleproxy.token_ttl)
        cat_dict = {
            "node_uuid": cat.node_uuid,
            "token": token,
            "access_url": cat.access_url,
        }
        return ConsoleAuthToken(**cat_dict)

    @wsme_pecan.wsexpose(ConsoleAuthToken, wtypes.text)
    def delete(self, node_uuid_or_name):
        context = pecan.request.context

        # get node
        client = ironic.get_ironic_client(context)
        node = client.node.get(node_uuid_or_name)
        if node is None:
            raise exception.NodeNotFound(
                uuid=node_uuid_or_name,
                resource_type="ironic_node",
                err="Node not found",
            )

        # disable all auth tokens for node
        cat_obj.ConsoleAuthToken.clean_console_tokens_for_node(node.uuid)
