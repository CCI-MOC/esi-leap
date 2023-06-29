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

from esi_leap.db import api as dbapi
from esi_leap.objects import base
from esi_leap.objects import fields

from oslo_config import cfg
from oslo_log import log as logging
from oslo_versionedobjects import base as versioned_objects_base

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


@versioned_objects_base.VersionedObjectRegistry.register
class Event(base.ESILEAPObject):
    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.IntegerField(),
        'event_type': fields.StringField(),
        'event_time': fields.DateTimeField(),
        'object_type': fields.StringField(nullable=True),
        'object_uuid': fields.StringField(nullable=True),
        'resource_type': fields.StringField(nullable=True),
        'resource_uuid': fields.StringField(nullable=True),
        'lessee_id': fields.StringField(nullable=True),
        'owner_id': fields.StringField(nullable=True),
    }

    @classmethod
    def get_all(cls, filters, context=None):
        db_events = cls.dbapi.event_get_all(filters)
        return cls._from_db_object_list(context, db_events)

    def create(self, context=None):
        updates = self.obj_get_changes()

        LOG.info('Creating event')
        db_event = self.dbapi.event_create(updates)
        self._from_db_object(context, self, db_event)
