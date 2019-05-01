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

from oslo_context import context as ctx
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_service import service
from oslo_utils import timeutils

from esi_leap.common import statuses
import esi_leap.conf
from esi_leap.db import api as db_api
from esi_leap.manager import utils
from esi_leap.objects import lease_request
from esi_leap.objects import policy_node


CONF = esi_leap.conf.CONF
EVENT_INTERVAL = 10
LOG = logging.getLogger(__name__)


class ManagerService(service.Service):
    def __init__(self):
        super(ManagerService, self).__init__()
        LOG.info("Creating esi-leap manager RPC server")
        self._server = messaging.get_rpc_server(
            target=utils.get_target(),
            transport=messaging.get_rpc_transport(CONF),
            endpoints=[ManagerEndpoint()],
            executor='eventlet',
        )
        self._context = ctx.RequestContext(
            auth_token=None,
            project_id=None,
            is_admin=True,
            overwrite=False)

    def start(self):
        super(ManagerService, self).start()
        LOG.info("Starting esi-leap manager RPC server")
        self.tg.add_thread(self._server.start)
        LOG.info("Starting _fulfill_leases periodic job")
        self.tg.add_timer(300, self._fulfill_leases)
        LOG.info("Starting _expire_or_cancel_leases periodic job")
        self.tg.add_timer(60, self._expire_or_cancel_leases)
        LOG.info("Starting _expire_policy_node_leases periodic job")
        self.tg.add_timer(60, self._expire_policy_node_leases)
        LOG.info("Starting _expire_policy_nodes periodic job")
        self.tg.add_timer(60, self._expire_policy_nodes)

    def stop(self):
        super(ManagerService, self).stop()
        LOG.info("Shutting down esi-leap manager RPC server")
        self._server.stop()

    def _fulfill_leases(self):
        LOG.info("Running _fulfill_leases")
        leases = lease_request.LeaseRequest.get_all_by_status(
            self._context, statuses.PENDING)
        for lease in leases:
            LOG.info("Trying to fulfill lease %s", lease.uuid)
            lease.fulfill(self._context)

    def _expire_or_cancel_leases(self):
        LOG.info("Running _expire_or_cancel_leases")
        pending_leases = lease_request.LeaseRequest.get_all_by_status(
            self._context, statuses.PENDING)
        for lease in pending_leases:
            if lease.cancel_date and lease.cancel_date <= timeutils.utcnow():
                LOG.info("Cancelling lease %s", lease.uuid)
                lease.expire_or_cancel(self._context, statuses.CANCELLED)

        fulfilled_leases = lease_request.LeaseRequest.get_all_by_status(
            self._context, statuses.FULFILLED)
        expired_leases = lease_request.LeaseRequest.get_all_by_status(
            self._context, statuses.DEGRADED)
        for lease in fulfilled_leases + expired_leases:
            if lease.expiration_date and \
               lease.expiration_date <= timeutils.utcnow():
                LOG.info("Expiring lease %s", lease.uuid)
                lease.expire_or_cancel(self._context)

    def _expire_policy_node_leases(self):
        LOG.info("Running _expire_policy_node_leases")
        nodes = policy_node.PolicyNode.get_leased(self._context)
        for node in nodes:
            if node.lease_expiration_date and \
               node.lease_expiration_date <= timeutils.utcnow():
                LOG.info("Unassigning node %s from lease %s",
                         node.node_uuid, node.request_uuid)
                node.unassign_node(self._context)

    def _expire_policy_nodes(self):
        LOG.info("Running _expire_policy_nodes")
        nodes = policy_node.PolicyNode.get_all(self._context)
        for node in nodes:
            if node.expiration_date and \
               node.expiration_date <= timeutils.utcnow():
                LOG.info("Expiring node %s", node.node_uuid)
                node.destroy(self._context)


class ManagerEndpoint(object):
    target = utils.get_target()

    def get_policy(self, context, policy_uuid):
        return db_api.policy_get(ctx.RequestContext.from_dict(context),
                                 policy_uuid)
