from oslo_context import context as ctx
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_service import service

import esi_leap.conf
from esi_leap.db import api as db_api
from esi_leap.manager import utils

CONF = esi_leap.conf.CONF
EVENT_INTERVAL = 10
LOG = logging.getLogger(__name__)


class ManagerService(service.Service):
    def __init__(self):
        super(ManagerService, self).__init__()
        LOG.debug("Creating esi-leap manager RPC server")
        self._server = messaging.get_rpc_server(
            target=utils.get_target(),
            transport=messaging.get_rpc_transport(CONF),
            endpoints=[ManagerEndpoint()],
            executor='eventlet',
        )

    def start(self):
        super(ManagerService, self).start()
        LOG.debug("Starting esi-leap manager RPC server")
        self.tg.add_thread(self._server.start)
        # TODO: this will need to be implemented, this is a reminder as to how
        # self.tg.add_timer(EVENT_INTERVAL, self._lease_request_something)

    def stop(self):
        super(ManagerService, self).stop()
        LOG.debug("Shutting down esi-leap manager RPC server")
        self._server.stop()


class ManagerEndpoint(object):
    target = utils.get_target()

    def get_policy(self, context, policy_uuid):
        return db_api.policy_get(ctx.RequestContext.from_dict(context),
                                 policy_uuid)
