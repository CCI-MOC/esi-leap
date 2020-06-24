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
from esi_leap.db import api as dbapi
from esi_leap.objects import base
import esi_leap.objects.contract
from esi_leap.objects import fields
from esi_leap.resource_objects import resource_object_factory as ro_factory

from oslo_config import cfg
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
        db_offer = cls.dbapi.offer_get(context, offer_uuid)
        return cls._from_db_object(context, cls(), db_offer)

    @classmethod
    def get_all(cls, context, filters):
        db_offers = cls.dbapi.offer_get_all(context, filters)
        return cls._from_db_object_list(context, db_offers)

    def create(self, context=None):
        updates = self.obj_get_changes()
        db_offer = self.dbapi.offer_create(context, updates)
        self._from_db_object(context, self, db_offer)

    def destroy(self, context=None):
        self.dbapi.offer_destroy(context, self.uuid)
        self.obj_reset_changes()

    def save(self, context=None):
        updates = self.obj_get_changes()
        db_offer = self.dbapi.offer_update(
            context, self.uuid, updates)
        self._from_db_object(context, self, db_offer)

    def resource_object(self):
        return ro_factory.ResourceObjectFactory.get_resource_object(
            self.resource_type, self.resource_uuid)

    def expire(self, context=None):
        # make sure all related contracts are expired
        contracts = esi_leap.objects.contract.Contract.get_all_by_offer_uuid(
            context, self.uuid)
        for c in contracts:
            if c.status != statuses.EXPIRED:
                c.expire(context)

        # expire offer
        self.status = statuses.EXPIRED
        self.save(context)
