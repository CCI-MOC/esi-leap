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

import datetime

from esi_leap.common import keystone
from esi_leap.common import statuses
import esi_leap.conf
from esi_leap.manager import utils
from esi_leap.objects import lease as lease_obj
from esi_leap.objects import offer as offer_obj
from oslo_context import context as ctx
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_service import service
from oslo_utils import timeutils

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


CONF = esi_leap.conf.CONF
EVENT_INTERVAL = 60
EVENT_INTERVAL_LONG = 3600 * 24
LOG = logging.getLogger(__name__)


class ManagerService(service.Service):
    def __init__(self):
        super(ManagerService, self).__init__()
        LOG.info('Creating esi-leap manager RPC server')
        self._server = messaging.get_rpc_server(
            target=utils.get_target(),
            transport=messaging.get_rpc_transport(CONF),
            endpoints=[ManagerEndpoint()],
            executor='eventlet',
        )
        self._context = ctx.RequestContext(
            auth_token=None,
            project_id=None,
            overwrite=False)

    def start(self):
        super(ManagerService, self).start()
        LOG.info('Starting esi-leap manager RPC server')
        self.tg.add_thread(self._server.start)
        LOG.info('Starting _fulfill_leases periodic job')
        self.tg.add_timer(EVENT_INTERVAL, self._fulfill_leases)
        LOG.info('Starting _expire_leases periodic job')
        self.tg.add_timer(EVENT_INTERVAL, self._expire_leases)
        LOG.info('Starting _cancel_leases periodic job')
        self.tg.add_timer(EVENT_INTERVAL, self._cancel_leases)
        LOG.info('Starting _notify_lease_expire periodic job')
        self.tg.add_timer(EVENT_INTERVAL_LONG, self._notify_lease_expire)
        LOG.info('Starting _expire_offers periodic job')
        self.tg.add_timer(EVENT_INTERVAL, self._expire_offers)

    def stop(self):
        super(ManagerService, self).stop()
        LOG.info('Shutting down esi-leap manager RPC server')
        self._server.stop()

    def _fulfill_leases(self):
        LOG.info('Checking for leases to fulfill')
        leases = lease_obj.Lease.get_all(
            {'status': [statuses.CREATED, statuses.WAIT_FULFILL]},
            self._context)
        now = timeutils.utcnow()
        for lease in leases:
            if lease.start_time <= now and now <= lease.end_time:
                try:
                    LOG.info('Fulfilling lease %s', lease.uuid)
                    lease.fulfill(self._context)
                except Exception as e:
                    LOG.info('Error fulfilling lease: %s: %s' %
                             (type(e).__name__, e))
                    LOG.info('Setting lease status to ERROR')
                    lease.status = statuses.ERROR
                    lease.save()

    def _expire_leases(self):
        LOG.info('Checking for expiring leases')
        leases = lease_obj.Lease.get_all(
            {'status': [statuses.ACTIVE, statuses.CREATED,
                        statuses.WAIT_EXPIRE, statuses.WAIT_FULFILL]},
            self._context)
        now = timeutils.utcnow()
        for lease in leases:
            if lease.end_time <= now:
                try:
                    LOG.info('Expiring lease %s', lease.uuid)
                    lease.expire(self._context)
                except Exception as e:
                    LOG.info('Error expiring lease: %s: %s' %
                             (type(e).__name__, e))
                    LOG.info('Setting lease status to ERROR')
                    lease.status = statuses.ERROR
                    lease.save()

    def _cancel_leases(self):
        LOG.info('Checking for leases to cancel')
        leases = lease_obj.Lease.get_all(
            {'status': [statuses.WAIT_CANCEL]}, self._context)
        for lease in leases:
            try:
                LOG.info('Cancelling lease %s', lease.uuid)
                lease.cancel()
            except Exception as e:
                LOG.info('Error cancelling lease: %s: %s' %
                         (type(e).__name__, e))
                LOG.info('Setting lease status to ERROR')
                lease.status = statuses.ERROR
                lease.save()

    def _expire_offers(self):
        LOG.info('Checking for expiring offers')
        offers = offer_obj.Offer.get_all({'status': statuses.OFFER_CAN_DELETE},
                                         self._context)

        for offer in offers:
            if offer.end_time and offer.end_time <= timeutils.utcnow():
                try:
                    LOG.info('Expiring offer %s for %s %s',
                             offer.uuid, offer.resource_type,
                             offer.resource_uuid)
                    offer.expire(self._context)
                except Exception as e:
                    LOG.info('Error expiring offer: %s: %s' %
                             (type(e).__name__, e))
                    offer.status = statuses.ERROR
                    offer.save()

    def _notify_lease_expire(self):
        LOG.info('Checking for leases expire soon')
        leases = lease_obj.Lease.get_all(
            {'status': [statuses.ACTIVE, statuses.CREATED,
                        statuses.WAIT_EXPIRE, statuses.WAIT_FULFILL]},
            self._context)
        now = timeutils.utcnow()
        for lease in leases:
            if lease.end_time - now <= \
                    datetime.timedelta(CONF.api.lease_warning_days):
                try:
                    LOG.info('Lease %s is expiring in %s day(s)' %
                             (lease.uuid, CONF.api.lease_warning_days))
                    if CONF.api.enable_email:
                        to_email = keystone.get_project_email(lease.project_id)
                        if not to_email:
                            LOG.info('No email linked to project %s. '
                                     'Not sending email notification',
                                     lease.project_id)
                        else:
                            email_body = f"Hi project {lease.project_id}," \
                                         f"\n\n" \
                                         f"We would like to inform you that" \
                                         f" your lease: {lease.uuid} " \
                                         f"will expire on {lease.end_time}." \
                                         f" To ensure " \
                                         f"the continuity of your data, " \
                                         f"please take the following steps:" \
                                         f"\n\n" \
                                         f"1. Save any important data" \
                                         f" associated with this resource." \
                                         f"\n" \
                                         f"2. If you wish to" \
                                         f" extend your lease," \
                                         f" please contact ESI admin team." \
                                         f"\n\n" \
                                         f"Thank you!" \
                                         f"\n\n" \
                                         f"ESI Admin Team"
                            self._send_email(to_email, email_body)
                except Exception as e:
                    LOG.info('Error sending lease expire '
                             'email notification: %s: %s' %
                             (type(e).__name__, e))

    def _send_email(self, to_email, email_body):
        try:
            msg = MIMEMultipart()
            msg['From'] = CONF.api.email_sender
            msg['To'] = to_email
            msg['Subject'] = '[ESI]Lease expires soon'
            msg.attach(MIMEText(email_body, 'plain'))
            server = smtplib.SMTP(CONF.api.SMTP_server)
            server.sendmail(CONF.api.email_sender, to_email,
                            msg.as_string())
            server.quit()
            LOG.info("Email sent successfully to %s", to_email)
        except Exception as e:
            LOG.info('Email not sent: %s: %s' %
                     (type(e).__name__, e))


class ManagerEndpoint(object):
    target = utils.get_target()
