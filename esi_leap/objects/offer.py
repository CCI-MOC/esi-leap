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

from oslo_versionedobjects import base as versioned_objects_base

from esi_leap.common import statuses
from esi_leap.db import api as dbapi
from esi_leap.objects import base
import esi_leap.objects.contract
from esi_leap.objects import fields
from esi_leap.resource_objects import resource_object_factory as ro_factory
import json
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneauth1 import loading as ks_loading


@versioned_objects_base.VersionedObjectRegistry.register
class Offer(base.ESILEAPObject):
    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.IntegerField(),
        'uuid': fields.UUIDField(),
        'project_id': fields.StringField(),
        'resource_type': fields.StringField(),
        'resource_uuid': fields.StringField(),
        'start_date': fields.DateTimeField(nullable=True),
        'end_date': fields.DateTimeField(nullable=True),
        'status': fields.StringField(),
        'properties': fields.FlexibleDictField(nullable=True),
    }

    @classmethod
    def get(cls, context, offer_uuid):
        db_offer = cls.dbapi.offer_get(context, offer_uuid)
        return cls._from_db_object(context, cls(), db_offer)

    @classmethod
    def get_all(cls, context):
        db_offers = cls.dbapi.offer_get_all(context)
        return cls._from_db_object_list(context, db_offers)

    @classmethod
    def get_all_by_project_id(cls, context, project_id):
        db_offers = cls.dbapi.offer_get_all_by_project_id(
            context, project_id)
        return cls._from_db_object_list(context, db_offers)

    @classmethod
    def get_all_by_status(cls, context, status):
        db_offers = cls.dbapi.offer_get_all_by_status(
            context, status)
        return cls._from_db_object_list(context, db_offers)

    @classmethod
    def send(cls, context, offer_uuid):
        o = Offer.get(context, offer_uuid)

        auth = v3.Password(auth_url='http://localhost:5000/v3',
                           username='flocx-provider',
                           password='password',
                           project_name='service',
                           user_domain_id='default',
                           project_domain_id='default')
        sess = session.Session(auth=auth)
        
        marketplace_offer_dict = o.to_marketplace_dict()

        response = sess.post(
            'http://localhost:8081/offer',
            data=json.dumps(marketplace_offer_dict))

        return response

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

    def to_marketplace_dict(self):
        # modifiy the offer data in order to be compatible with flocx-market POST offer api
        # change fields name
        offer_dict = self.to_dict()
        offer_dict['start_time'] = offer_dict.pop('start_date').isoformat()
        offer_dict['end_time'] = offer_dict.pop('end_date').isoformat()
        offer_dict['server_config'] = offer_dict.pop('properties')
        offer_dict['server_id'] = offer_dict.pop('resource_uuid')
        offer_dict['provider_id'] = offer_dict.pop('uuid')
        # remove unnecessary feilds
        offer_dict.pop('created_at')
        offer_dict.pop('updated_at')
        offer_dict.pop('id')
        offer_dict.pop('project_id')
        offer_dict.pop('resource_type')
        # fake fields
        offer_dict['creator_id'] = 'Alice1992'
        offer_dict['marketplace_date_created'] = '2016-07-16T19:20:30'
        offer_dict['cost'] = 11.5

        return offer_dict