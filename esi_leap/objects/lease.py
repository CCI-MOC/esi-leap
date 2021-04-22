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
from esi_leap.resource_objects import resource_object_factory as ro_factory

from oslo_config import cfg
from oslo_versionedobjects import base as versioned_objects_base

CONF = cfg.CONF


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

        @utils.synchronized(
            utils.get_resource_lock_name(updates['resource_type'],
                                         updates['resource_uuid']),
            external=True)
        def _create_lease():

            if updates['start_time'] >= updates['end_time']:
                raise exception.InvalidTimeRange(
                    resource='lease',
                    start_time=str(updates['start_time']),
                    end_time=str(updates['end_time'])
                    )

            if 'offer_uuid' in updates:
                related_offer = offer_obj.Offer.get(updates['offer_uuid'])

                if related_offer.status != statuses.AVAILABLE:
                    raise exception.OfferNotAvailable(
                        offer_uuid=related_offer.uuid,
                        status=related_offer.status)

                related_offer.verify_availability(updates['start_time'],
                                                  updates['end_time'])
            else:
                ro = ro_factory.ResourceObjectFactory.get_resource_object(
                    updates['resource_type'], updates['resource_uuid'])
                ro.verify_availability(updates['start_time'],
                                       updates['end_time'])

            db_lease = self.dbapi.lease_create(updates)
            self._from_db_object(context, self, db_lease)

        _create_lease()

    def cancel(self):
        resource = self.resource_object()
        if resource.get_lease_uuid() == self.uuid:
            resource.expire_lease(self)

        self.status = statuses.CANCELLED
        self.expire_time = datetime.datetime.now()
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
        @utils.synchronized(utils.get_resource_lock_name(self.resource_type,
                                                         self.resource_uuid),
                            external=True)
        def _fulfill_lease():

            resource = self.resource_object()
            resource.set_lease(self)

            # activate lease
            self.status = statuses.ACTIVE
            self.fulfill_time = datetime.datetime.now()
            self.save(context)

        _fulfill_lease()

    def expire(self, context=None):
        # unassign resource
        resource = self.resource_object()
        if resource.get_lease_uuid() == self.uuid:
            resource.expire_lease(self)

        # expire lease
        self.status = statuses.EXPIRED
        self.expire_time = datetime.datetime.now()
        self.save(context)

    def resource_object(self):
        return ro_factory.ResourceObjectFactory.get_resource_object(
            self.resource_type, self.resource_uuid)
