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

from keystoneauth1 import loading as ks_loading
from keystoneauth1 import service_token
from keystoneauth1 import token_endpoint

from ironicclient import client as ironic_client

import esi_leap.conf


CONF = esi_leap.conf.CONF
_cached_ironic_client = None


def get_ironic_client(context=None):
    session = ks_loading.load_session_from_conf_options(CONF, 'ironic')
    service_auth = ks_loading.load_auth_from_conf_options(CONF, 'ironic')

    # use user context if provided
    user_auth = None
    if context:
        endpoint = ks_loading.load_adapter_from_conf_options(
            CONF, 'ironic', session=session, auth=service_auth).get_endpoint()
        user_auth = service_token.ServiceTokenAuthWrapper(
            user_auth=token_endpoint.Token(endpoint, context.auth_token),
            service_auth=service_auth)
    sess = ks_loading.load_session_from_conf_options(
        CONF, 'ironic', auth=user_auth or service_auth)

    kwargs = {'os_ironic_api_version': '1.65'}
    cli = ironic_client.get_client(1, session=sess, **kwargs)
    return cli


def get_node_list(context=None):
    return get_ironic_client(context).node.list(detail=True)


def get_node(node_uuid, node_list=None):
    if node_list is None:
        node = get_ironic_client().node.get(node_uuid)
    else:
        node = next((n for n in node_list if n.uuid == node_uuid), None)
    return node
