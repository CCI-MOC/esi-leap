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
from oslo_config import cfg
from oslo_log import log as logging
from oslo_versionedobjects import base as versioned_objects_base

from esi_leap.common import exception
from esi_leap.common import statuses
from esi_leap.common import utils
from esi_leap.db import api as dbapi
from esi_leap.objects import base
from esi_leap.objects import fields
from esi_leap.objects import lease as lease_obj
from esi_leap.objects import offer as offer_obj
from esi_leap.resource_objects import resource_object_factory as ro_factory


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


@versioned_objects_base.VersionedObjectRegistry.register
class OwnerChange(base.ESILEAPObject):
    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.IntegerField(),
        'uuid': fields.UUIDField(),
        'from_owner_id': fields.StringField(),
        'to_owner_id': fields.StringField(),
        'resource_type': fields.StringField(),
        'resource_uuid': fields.StringField(),
        'start_time': fields.DateTimeField(nullable=True),
        'end_time': fields.DateTimeField(nullable=True),
        'fulfill_time': fields.DateTimeField(nullable=True),
        'expire_time': fields.DateTimeField(nullable=True),
        'status': fields.StringField(),
    }

    @classmethod
    def get(cls, owner_change_uuid, context=None):
        db_owner_change = cls.dbapi.owner_change_get_by_uuid(owner_change_uuid)
        if db_owner_change:
            return cls._from_db_object(context, cls(), db_owner_change)

    @classmethod
    def get_all(cls, filters, context=None):
        db_owner_changes = cls.dbapi.owner_change_get_all(filters)
        return cls._from_db_object_list(context, db_owner_changes)

    def create(self, context=None):
        updates = self.obj_get_changes()

        @utils.synchronized(
            utils.get_resource_lock_name(
                updates['resource_type'], updates['resource_uuid']),
            external=True)
        def _create_owner_change():

            if updates['start_time'] >= updates['end_time']:
                raise exception.InvalidTimeRange(
                    resource='owner_change',
                    start_time=str(updates['start_time']),
                    end_time=str(updates['end_time'])
                )

            ro = ro_factory.ResourceObjectFactory.get_resource_object(
                updates['resource_type'], updates['resource_uuid'])
            ro.verify_availability(updates['start_time'],
                                   updates['end_time'],
                                   is_owner_change=True)

            db_owner_change = self.dbapi.owner_change_create(updates)
            self._from_db_object(context, self, db_owner_change)

        _create_owner_change()

    def fulfill(self, context=None):
        @utils.synchronized(utils.get_resource_lock_name(self.resource_type,
                                                         self.resource_uuid),
                            external=True)
        def _fulfill_owner_change():
            LOG.info("Setting owner of %s %s from %s to %s",
                     self.resource_type, self.resource_uuid,
                     self.from_owner_id, self.to_owner_id)

            resource = self.resource_object()
            resource.set_owner(self.to_owner_id)

            # activate owner change
            self.status = statuses.ACTIVE
            self.fulfill_time = datetime.datetime.now()
            self.save(context)

        _fulfill_owner_change()

    def cancel(self):
        offers_to_cancel = self.offers()
        for offer in offers_to_cancel:
            offer.cancel()
        leases_to_cancel = self.leases()
        for lease in leases_to_cancel:
            lease.cancel()

        @utils.synchronized(utils.get_resource_lock_name(self.resource_type,
                                                         self.resource_uuid))
        def _cancel_owner_change():
            LOG.info("Setting owner of %s %s back to %s",
                     self.resource_type, self.resource_uuid,
                     self.from_owner_id)

            resource = self.resource_object()
            resource.set_owner(self.from_owner_id)

            self.status = statuses.DELETED
            self.expire_time = datetime.datetime.now()
            self.save(None)

        _cancel_owner_change()

    def expire(self, context=None):
        offers_to_cancel = self.offers()
        for offer in offers_to_cancel:
            offer.cancel()
        leases_to_cancel = self.leases()
        for lease in leases_to_cancel:
            lease.cancel()

        @utils.synchronized(utils.get_resource_lock_name(self.resource_type,
                                                         self.resource_uuid))
        def _expire_owner_change():
            LOG.info("Setting owner of %s %s from %s back to %s",
                     self.resource_type, self.resource_uuid,
                     self.to_owner_id, self.from_owner_id)

            resource = self.resource_object()
            resource.set_owner(self.from_owner_id)

            self.status = statuses.EXPIRED
            self.expire_time = datetime.datetime.now()
            self.save(context)

        _expire_owner_change()

    def destroy(self):
        self.dbapi.owner_change_destroy(self.uuid)
        self.obj_reset_changes()

    def save(self, context=None):
        updates = self.obj_get_changes()
        db_owner_change = self.dbapi.owner_change_update(
            self.uuid, updates)
        self._from_db_object(context, self, db_owner_change)

    def offers(self):
        return offer_obj.Offer.get_all({
            'project_id': self.to_owner_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'time_filter_type': 'within',
            'status': statuses.AVAILABLE
        })

    def leases(self):
        return lease_obj.Lease.get_all({
            'owner_id': self.to_owner_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'time_filter_type': 'within',
            'status': [statuses.CREATED, statuses.ACTIVE]
        })

    def resource_object(self):
        return ro_factory.ResourceObjectFactory.get_resource_object(
            self.resource_type, self.resource_uuid)
