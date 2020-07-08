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
from esi_leap.objects import fields
import esi_leap.objects.offer
from oslo_config import cfg
from oslo_utils import uuidutils
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
        db_contract = cls.dbapi.contract_get(contract_uuid)
        return cls._from_db_object(context, cls(), db_contract)

    @classmethod
    def get_all(cls, context, filters):
        db_contracts = cls.dbapi.contract_get_all(filters)
        return cls._from_db_object_list(context, db_contracts)

    def create(self, context=None):
        updates = self.obj_get_changes()
        updates['uuid'] = uuidutils.generate_uuid()

        if 'offer_uuid' not in updates:
            raise exception.ContractNoOfferUUID()

        related_offer = self.dbapi.offer_get(updates['offer_uuid'])
        if related_offer is None:
            raise exception.OfferNotFound(offer_uuid=updates['offer_uuid'])

        if related_offer.status != statuses.AVAILABLE:
            raise exception.OfferNotAvailable(offer_uuid=related_offer.uuid,
                                              status=related_offer.status)

        if 'start_time' not in updates:
            updates['start_time'] = datetime.datetime.now()

        if 'end_time' not in updates:
            q = self.dbapi.offer_get_first_availability(related_offer,
                                                        updates['start_time'])
            if q is None:
                updates['end_time'] = related_offer.end_time
            else:
                updates['end_time'] = q.start_time

        self.dbapi.offer_verify_availability(related_offer,
                                             updates['start_time'],
                                             updates['end_time'])

        db_contract = self.dbapi.contract_create(updates)
        self._from_db_object(context, self, db_contract)

    def cancel(self):
        o = esi_leap.objects.offer.Offer.get(None, self.offer_uuid)

        resource = o.resource_object()
        if resource.get_contract_uuid() == self.uuid:
            resource.set_contract(None)

        self.status = statuses.CANCELLED
        self.save(None)

    def destroy(self):
        self.dbapi.contract_destroy(self.uuid)
        self.obj_reset_changes()

    def save(self, context=None):
        updates = self.obj_get_changes()
        db_contract = self.dbapi.contract_update(
            self.uuid, updates)
        self._from_db_object(context, self, db_contract)

    def fulfill(self, context=None):
        # fulfill resource
        o = esi_leap.objects.offer.Offer.get(
            context, self.offer_uuid)
        resource = o.resource_object()
        resource.set_contract(self)

        # expire contract
        self.status = statuses.ACTIVE
        self.save(context)

    def expire(self, context=None):
        # unassign resource
        o = esi_leap.objects.offer.Offer.get(
            context, self.offer_uuid)
        if o.status != statuses.AVAILABLE:
            raise exception.OfferNotAvailable(offer_uuid=o.uuid,
                                              status=o.status)

        resource = o.resource_object()
        if resource.get_contract_uuid() == self.uuid:
            resource.set_contract(None)

        # expire contract
        self.status = statuses.EXPIRED
        self.save(context)
