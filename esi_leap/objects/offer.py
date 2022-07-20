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
from esi_leap.objects import lease as lease_obj
from esi_leap.resource_objects import get_resource_object

from oslo_config import cfg
from oslo_log import log as logging
from oslo_versionedobjects import base as versioned_objects_base

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


@versioned_objects_base.VersionedObjectRegistry.register
class Offer(base.ESILEAPObject):
    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.IntegerField(),
        'name': fields.StringField(nullable=True),
        'uuid': fields.UUIDField(),
        'project_id': fields.StringField(),
        'lessee_id': fields.StringField(nullable=True),
        'resource_type': fields.StringField(),
        'resource_uuid': fields.StringField(),
        'start_time': fields.DateTimeField(nullable=True),
        'end_time': fields.DateTimeField(nullable=True),
        'status': fields.StringField(),
        'properties': fields.FlexibleDictField(nullable=True),
        'parent_lease_uuid': fields.UUIDField(nullable=True),
    }

    @classmethod
    def get(cls, offer_uuid, context=None):
        db_offer = cls.dbapi.offer_get_by_uuid(offer_uuid)
        if db_offer:
            return cls._from_db_object(context, cls(), db_offer)

    @classmethod
    def get_all(cls, filters, context=None):
        db_offers = cls.dbapi.offer_get_all(filters)
        return cls._from_db_object_list(context, db_offers)

    def get_availabilities(self):

        if self.status != statuses.AVAILABLE:
            return []

        conflicts = self.dbapi.offer_get_conflict_times(self)
        now = datetime.datetime.now()
        start_time = self.start_time if self.start_time >= now else now

        if conflicts:
            # if the conflicts are all in the past:
            if conflicts[-1][1] <= start_time:
                avails = [[start_time, self.end_time]]
            else:
                # if the offer starts in the future or
                # the first conflict time is in the future,
                # add the $start_time and first conflict start_time
                # in the array
                if start_time < conflicts[0][0]:
                    times = [start_time, conflicts[0][0]]
                    for i in range(len(conflicts) - 1):
                        times.append(conflicts[i][1])
                        times.append(conflicts[i + 1][0])
                else:
                    times = []
                    for i in range(len(conflicts) - 1):
                        # Find the conflict timeframe that started
                        # in the past and will end in the future.
                        # add all times after this
                        if (conflicts[i][0] <= start_time and
                            conflicts[i][1] > start_time) \
                            or conflicts[i][0] > start_time:
                            times.append(conflicts[i][1])
                            times.append(conflicts[i + 1][0])

                times.append(conflicts[-1][1])
                times.append(self.end_time)

                i = 0
                while i < len(times) - 1:
                    if times[i] == times[i + 1]:
                        times.pop(i)
                        times.pop(i)
                    else:
                        i += 1

                avails = [[times[j], times[j + 1]]
                          for j in range(0, len(times) - 1, 2)]

        else:
            avails = [[start_time, self.end_time]]

        return avails

    def get_first_availability(self, start):
        return self.dbapi.offer_get_first_availability(self.uuid, start)

    def create(self, context=None):
        updates = self.obj_get_changes()

        with utils.lock(utils.get_resource_lock_name(updates['resource_type'],
                                                     updates['resource_uuid']),
                        external=True):
            LOG.info('Creating offer')
            if updates['start_time'] >= updates['end_time']:
                raise exception.InvalidTimeRange(
                    resource='offer',
                    start_time=str(updates['start_time']),
                    end_time=str(updates['end_time'])
                )

            if updates.get('parent_lease_uuid'):
                # offer is a child of an existing lease
                parent_lease = lease_obj.Lease.get(
                    updates['parent_lease_uuid'])

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

            db_offer = self.dbapi.offer_create(updates)
            self._from_db_object(context, self, db_offer)

    def cancel(self):
        LOG.info('Deleting offer %s', self.uuid)
        leases = lease_obj.Lease.get_all(
            {'offer_uuid': self.uuid,
             'status': statuses.LEASE_CAN_DELETE},
            None)
        for lease in leases:
            lease.cancel()

        with utils.lock(utils.get_resource_lock_name(self.resource_type,
                                                     self.resource_uuid),
                        external=True):
            self.status = statuses.DELETED
            self.save(None)

    def expire(self, context=None):
        LOG.info('Expiring offer %s', self.uuid)
        leases = lease_obj.Lease.get_all(
            {'offer_uuid': self.uuid,
             'status': statuses.LEASE_CAN_DELETE},
            None)
        for lease in leases:
            lease.expire(context)

        with utils.lock(utils.get_resource_lock_name(self.resource_type,
                                                     self.resource_uuid),
                        external=True):
            self.status = statuses.EXPIRED
            self.save(context)

    def verify_availability(self, start_time, end_time):
        return self.dbapi.offer_verify_availability(
            self, start_time, end_time)

    def destroy(self):
        self.dbapi.offer_destroy(self.uuid)
        self.obj_reset_changes()

    def save(self, context=None):
        updates = self.obj_get_changes()
        db_offer = self.dbapi.offer_update(
            self.uuid, updates)
        self._from_db_object(context, self, db_offer)

    def resource_object(self):
        return get_resource_object(self.resource_type, self.resource_uuid)
