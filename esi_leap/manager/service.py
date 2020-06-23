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


from esi_leap.common import statuses
import esi_leap.conf
from esi_leap.manager import utils
from esi_leap.objects import contract
from esi_leap.objects import offer
from oslo_context import context as ctx
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_service import service
from oslo_utils import timeutils

CONF = esi_leap.conf.CONF
EVENT_INTERVAL = 60
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
        LOG.info("Starting _fulfill_contracts periodic job")
        self.tg.add_timer(EVENT_INTERVAL, self._fulfill_contracts)
        LOG.info("Starting _expire_contracts periodic job")
        self.tg.add_timer(EVENT_INTERVAL, self._expire_contracts)
        LOG.info("Starting _expire_offers periodic job")
        self.tg.add_timer(EVENT_INTERVAL, self._expire_offers)
        LOG.info("Starting _retrieve_contracts periodic job")
        self.tg.add_timer(EVENT_INTERVAL, self._retrieve_contracts)

    def stop(self):
        super(ManagerService, self).stop()
        LOG.info("Shutting down esi-leap manager RPC server")
        self._server.stop()

    def _fulfill_contracts(self):
        LOG.info("Checking for contracts to fulfill")
        contracts = contract.Contract.get_all_by_status(
            self._context, statuses.OPEN)
        for c in contracts:
            if c.start_time and \
               c.start_time <= timeutils.utcnow():
                LOG.info("Fulfilling contract %s", c.uuid)
                c.fulfill(self._context)

    def _expire_contracts(self):
        LOG.info("Checking for expiring contracts")
        contracts = contract.Contract.get_all_by_status(
            self._context, statuses.FULFILLED)
        for c in contracts:
            if c.end_time and \
               c.end_time <= timeutils.utcnow():
                LOG.info("Expiring contract %s", c.uuid)
                c.expire(self._context)

    def _expire_offers(self):
        LOG.info("Checking for expiring offers")
        offers = offer.Offer.get_all_by_status(
            self._context, statuses.AVAILABLE)
        for o in offers:
            if o.end_time and \
               o.end_time <= timeutils.utcnow():
                LOG.info("Expiring offer %s for %s %s",
                         o.uuid, o.resource_type, o.resource_uuid)
                o.expire(self._context)


class ManagerEndpoint(object):
    target = utils.get_target()
