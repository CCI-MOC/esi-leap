import oslo_messaging as messaging

import esi_leap.conf
from esi_leap.manager import utils

CONF = esi_leap.conf.CONF


class ManagerRPCAPI(object):
    """Client side of the manager RPC API

    API version history:

    * 1.0 - Initial version.
    """

    def __init__(self):
        self._client = messaging.RPCClient(
            target=utils.get_target(),
            transport=messaging.get_rpc_transport(CONF),
        )

    def get_policy(self, context, policy_uuid):
        cctxt = self._client.prepare()
        return cctxt.call(context, 'get_policy', policy_uuid=policy_uuid)
