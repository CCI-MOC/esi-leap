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
from esi_leap.objects import leasable_resource
from esi_leap.objects import lease_request


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
        LOG.info("Starting _monitor_leases periodic job")
        self.tg.add_timer(60, self._monitor_leases)
        LOG.info("Starting _monitor_leasable_resources periodic job")
        self.tg.add_timer(60, self._monitor_leasable_resources)

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

    def _monitor_leases(self):
        LOG.info("Checking for cancelled leases")
        pending_leases = lease_request.LeaseRequest.get_all_by_status(
            self._context, statuses.PENDING)
        for lease in pending_leases:
            if lease.cancel_date and lease.cancel_date <= timeutils.utcnow():
                LOG.info("Cancelling lease %s", lease.uuid)
                lease.expire_or_cancel(self._context, statuses.CANCELLED)

        LOG.info("Checking for expired leases")
        fulfilled_leases = lease_request.LeaseRequest.get_all_by_status(
            self._context, statuses.FULFILLED)
        expired_leases = lease_request.LeaseRequest.get_all_by_status(
            self._context, statuses.DEGRADED)
        for lease in fulfilled_leases + expired_leases:
            if lease.expiration_date and \
               lease.expiration_date <= timeutils.utcnow():
                LOG.info("Expiring lease %s", lease.uuid)
                lease.expire_or_cancel(self._context)

    def _monitor_leasable_resources(self):
        LOG.info("Checking for expired leasable resources")
        resources = leasable_resource.LeasableResource.get_all(self._context)
        for resource in resources:
            if resource.expiration_date and \
               resource.expiration_date <= timeutils.utcnow():
                LOG.info("Expiring node %s", resource.node_uuid)
                resource.destroy(self._context)

        LOG.info("Checking for expired leasable_resource leases")
        resources = leasable_resource.LeasableResource.get_leased(
            self._context)
        for resource in resources:
            if resource.lease_expiration_date and \
               resource.lease_expiration_date <= timeutils.utcnow():
                LOG.info("Unassigning node %s from lease %s",
                         resource.resource_uuid, resource.request_uuid)
                resource.unassign(self._context)


class ManagerEndpoint(object):
    target = utils.get_target()

    def get_policy(self, context, policy_uuid):
        return db_api.policy_get(ctx.RequestContext.from_dict(context),
                                 policy_uuid)
