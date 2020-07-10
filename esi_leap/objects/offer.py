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
from esi_leap.db import api as dbapi
from esi_leap.objects import base
import esi_leap.objects.contract
from esi_leap.objects import fields
from esi_leap.resource_objects import resource_object_factory as ro_factory

from oslo_config import cfg
from oslo_utils import uuidutils
from oslo_versionedobjects import base as versioned_objects_base

CONF = cfg.CONF


@versioned_objects_base.VersionedObjectRegistry.register
class Offer(base.ESILEAPObject):
    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.IntegerField(),
        'uuid': fields.UUIDField(),
        'project_id': fields.StringField(),
        'resource_type': fields.StringField(),
        'resource_uuid': fields.StringField(),
        'start_time': fields.DateTimeField(nullable=True),
        'end_time': fields.DateTimeField(nullable=True),
        'status': fields.StringField(),
        'properties': fields.FlexibleDictField(nullable=True),
    }

    @classmethod
    def get(cls, context, offer_uuid):
        db_offer = cls.dbapi.offer_get(offer_uuid)
        return cls._from_db_object(context, cls(), db_offer)

    @classmethod
    def get_all(cls, context, filters):
        db_offers = cls.dbapi.offer_get_all(filters)
        return cls._from_db_object_list(context, db_offers)

    def get_availabilities(self):

        if self.status != statuses.AVAILABLE:
            return []

        conflicts = self.dbapi.offer_get_conflict_times(self)

        if conflicts:
            a = [self.start_time, conflicts[0][0]]
            for i in range(len(conflicts) - 1):
                a.append(conflicts[i][1])
                a.append(conflicts[i + 1][0])
            a.append(conflicts[-1][1])
            a.append(self.end_time)

            i = 0
            while i < len(a) - 1:
                if a[i] == a[i + 1]:
                    a.pop(i)
                    a.pop(i)
                else:
                    i += 1

            a = [[a[j], a[j + 1]] for j in range(0, len(a) - 1, 2)]

        else:
            a = [[self.start_time, self.end_time]]

        return a

    def create(self, context=None):
        updates = self.obj_get_changes()

        updates['uuid'] = uuidutils.generate_uuid()

        if 'start_time' not in updates:
            updates['start_time'] = datetime.datetime.now()
        if 'end_time' not in updates:
            updates['end_time'] = datetime.datetime.max

        if updates['start_time'] >= updates['end_time']:
            raise exception.\
                InvalidTimeRange(resource="an offer",
                                 start_time=str(updates['start_time']),
                                 end_time=str(updates['end_time']))

        db_offer = self.dbapi.offer_create(updates)
        self._from_db_object(context, self, db_offer)

    def cancel(self):
        contracts = esi_leap.objects.contract.Contract.get_all(
            None, {'offer_uuid': self.uuid})
        for c in contracts:
            if c.status == statuses.CREATED or c.status == statuses.ACTIVE:
                c.cancel()

        self.status = statuses.CANCELLED
        self.save(None)

    def destroy(self):
        self.dbapi.offer_destroy(self.uuid)
        self.obj_reset_changes()

    def save(self, context=None):
        updates = self.obj_get_changes()
        db_offer = self.dbapi.offer_update(
            self.uuid, updates)
        self._from_db_object(context, self, db_offer)

    def resource_object(self):
        return ro_factory.ResourceObjectFactory.get_resource_object(
            self.resource_type, self.resource_uuid)

    def expire(self, context=None):
        # make sure all related contracts are expired
        contracts = esi_leap.objects.contract.Contract.get_all(
            None, {'offer_uuid': self.uuid})
        for c in contracts:
            if c.status != statuses.EXPIRED:
                c.expire(context)

        # expire offer
        self.status = statuses.EXPIRED
        self.save(context)
