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

from esi_leap.common import exception
from esi_leap.common import statuses
from esi_leap.common import utils
from esi_leap.db import api as dbapi
from esi_leap.objects import base
from esi_leap.objects import fields
from esi_leap.objects import offer as offer_obj
from esi_leap.resource_objects import get_resource_object

from oslo_config import cfg
from oslo_log import log as logging
from oslo_versionedobjects import base as versioned_objects_base

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


@versioned_objects_base.VersionedObjectRegistry.register
class Lease(base.ESILEAPObject):
    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.IntegerField(),
        'name': fields.StringField(nullable=True),
        'uuid': fields.UUIDField(),
        'project_id': fields.StringField(),
        'owner_id': fields.StringField(),
        'resource_type': fields.StringField(),
        'resource_uuid': fields.StringField(),
        'start_time': fields.DateTimeField(nullable=True),
        'end_time': fields.DateTimeField(nullable=True),
        'fulfill_time': fields.DateTimeField(nullable=True),
        'expire_time': fields.DateTimeField(nullable=True),
        'status': fields.StringField(),
        'properties': fields.FlexibleDictField(nullable=True),
        'offer_uuid': fields.UUIDField(nullable=True),
        'parent_lease_uuid': fields.UUIDField(nullable=True),
    }

    @classmethod
    def get(cls, lease_uuid, context=None):
        db_lease = cls.dbapi.lease_get_by_uuid(lease_uuid)
        if db_lease:
            return cls._from_db_object(context, cls(), db_lease)

    @classmethod
    def get_all(cls, filters, context=None):
        db_leases = cls.dbapi.lease_get_all(filters)
        return cls._from_db_object_list(context, db_leases)

    def create(self, context=None):
        updates = self.obj_get_changes()

        with utils.lock(utils.get_resource_lock_name(updates['resource_type'],
                                                     updates['resource_uuid']),
                        external=True):
            if updates['start_time'] >= updates['end_time']:
                raise exception.InvalidTimeRange(
                    resource='lease',
                    start_time=str(updates['start_time']),
                    end_time=str(updates['end_time'])
                    )

            # check availability
            if 'offer_uuid' in updates:
                # lease is being created from an offer
                related_offer = offer_obj.Offer.get(updates['offer_uuid'])

                if related_offer.status != statuses.AVAILABLE:
                    raise exception.OfferNotAvailable(
                        offer_uuid=related_offer.uuid,
                        status=related_offer.status)

                related_offer.verify_availability(updates['start_time'],
                                                  updates['end_time'])
            elif 'parent_lease_uuid' in updates:
                # lease is a child of an existing lease
                parent_lease = Lease.get(updates['parent_lease_uuid'])

                if parent_lease.status != statuses.ACTIVE:
                    raise exception.LeaseNotActive(
                        updates['parent_lease_uuid'])

                parent_lease.verify_child_availability(updates['start_time'],
                                                       updates['end_time'])
            else:
                ro = get_resource_object(updates['resource_type'],
                                         updates['resource_uuid'])
                ro.verify_availability(updates['start_time'],
                                       updates['end_time'])

            db_lease = self.dbapi.lease_create(updates)
            self._from_db_object(context, self, db_lease)

    def cancel(self):
        leases = Lease.get_all(
            {'parent_lease_uuid': self.uuid,
             'status': statuses.LEASE_CAN_DELETE},
            None)
        for lease in leases:
            lease.cancel()
        offers = offer_obj.Offer.get_all(
            {'parent_lease_uuid': self.uuid,
             'status': statuses.OFFER_CAN_DELETE},
            None)
        for offer in offers:
            offer.cancel()

        with utils.lock(utils.get_resource_lock_name(self.resource_type,
                                                     self.resource_uuid),
                        external=True):
            LOG.info('Deleting lease %s', self.uuid)
            try:
                resource = self.resource_object()
                if resource.get_lease_uuid() == self.uuid:
                    resource.expire_lease(self)
                    if self.parent_lease_uuid is not None:
                        parent_lease = Lease.get(self.parent_lease_uuid)
                        resource.set_lease(parent_lease)

                self.status = statuses.DELETED
                self.expire_time = datetime.datetime.now()
            except Exception as e:
                LOG.info('Error canceling lease: %s: %s' %
                         (type(e).__name__, e))
                LOG.info('Setting lease status to WAIT')
                self.status = statuses.WAIT_CANCEL
            self.save(None)

    def destroy(self):
        self.dbapi.lease_destroy(self.uuid)
        self.obj_reset_changes()

    def save(self, context=None):
        updates = self.obj_get_changes()
        db_lease = self.dbapi.lease_update(
            self.uuid, updates)
        self._from_db_object(context, self, db_lease)

    def fulfill(self, context=None):
        with utils.lock(utils.get_resource_lock_name(self.resource_type,
                                                     self.resource_uuid),
                        external=True):
            LOG.info('Fulfilling lease %s', self.uuid)
            try:
                resource = self.resource_object()
                resource.set_lease(self)

                # activate lease
                self.status = statuses.ACTIVE
                self.fulfill_time = datetime.datetime.now()
            except Exception as e:
                LOG.info('Error fulfilling lease: %s: %s' %
                         (type(e).__name__, e))
                LOG.info('Setting lease status to WAIT')
                self.status = statuses.WAIT_FULFILL
            self.save(context)

    def expire(self, context=None):
        leases = Lease.get_all(
            {'parent_lease_uuid': self.uuid,
             'status': statuses.LEASE_CAN_DELETE},
            None)
        for lease in leases:
            lease.expire(context)
        offers = offer_obj.Offer.get_all(
            {'parent_lease_uuid': self.uuid,
             'status': statuses.OFFER_CAN_DELETE},
            None)
        for offer in offers:
            offer.expire(context)

        with utils.lock(utils.get_resource_lock_name(self.resource_type,
                                                     self.resource_uuid),
                        external=True):
            LOG.info('Expiring lease %s', self.uuid)
            try:
                resource = self.resource_object()
                if resource.get_lease_uuid() == self.uuid:
                    resource.expire_lease(self)
                    if self.parent_lease_uuid is not None:
                        parent_lease = Lease.get(self.parent_lease_uuid)
                        resource.set_lease(parent_lease)
                # expire lease
                self.status = statuses.EXPIRED
                self.expire_time = datetime.datetime.now()
            except Exception as e:
                LOG.info('Error expiring lease: %s: %s' %
                         (type(e).__name__, e))
                LOG.info('Setting lease status to WAIT')
                self.status = statuses.WAIT_EXPIRE
            self.save(context)

    def resource_object(self):
        return get_resource_object(self.resource_type, self.resource_uuid)

    def verify_child_availability(self, start_time, end_time):
        return self.dbapi.lease_verify_child_availability(
            self, start_time, end_time)
