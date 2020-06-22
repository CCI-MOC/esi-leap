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
from esi_leap.objects import fields
import esi_leap.objects.offer
from oslo_config import cfg
from oslo_versionedobjects import base as versioned_objects_base

CONF = cfg.CONF


@versioned_objects_base.VersionedObjectRegistry.register
class Contract(base.ESILEAPObject):
    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.IntegerField(),
        'uuid': fields.UUIDField(),
        'project_id': fields.StringField(),
        'start_time': fields.DateTimeField(nullable=True),
        'end_time': fields.DateTimeField(nullable=True),
        'status': fields.StringField(),
        'properties': fields.FlexibleDictField(nullable=True),
        'offer_uuid': fields.UUIDField(),
    }

    @classmethod
    def get(cls, context, contract_uuid):
        db_contract = cls.dbapi.contract_get(context, contract_uuid)
        return cls._from_db_object(context, cls(), db_contract)

    @classmethod
    def get_all(cls, context, filters):
        db_contracts = cls.dbapi.contract_get_all(context, filters)
        return cls._from_db_object_list(context, db_contracts)

    def create(self, context=None):
        updates = self.obj_get_changes()
        db_contract = self.dbapi.contract_create(context, updates)
        self._from_db_object(context, self, db_contract)

    def destroy(self, context=None):
        self.dbapi.contract_destroy(context, self.uuid)
        self.obj_reset_changes()

    def save(self, context=None):
        updates = self.obj_get_changes()
        db_contract = self.dbapi.contract_update(
            context, self.uuid, updates)
        self._from_db_object(context, self, db_contract)

    def fulfill(self, context=None):
        # fulfill resource
        o = esi_leap.objects.offer.Offer.get(
            context, self.offer_uuid)
        resource = o.resource_object()
        resource.set_contract(self)

        # expire contract
        self.status = statuses.FULFILLED
        self.save(context)

    def expire(self, context=None):
        # unassign resource
        o = esi_leap.objects.offer.Offer.get(
            context, self.offer_uuid)
        resource = o.resource_object()
        if resource.get_contract_uuid() == self.uuid:
            resource.set_contract(None)

        # expire contract
        self.status = statuses.EXPIRED
        self.save(context)
