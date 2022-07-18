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
from oslo_log import log
from oslo_versionedobjects import base as object_base

from esi_leap.objects import fields as object_fields


LOG = log.getLogger(__name__)


class ESILEAPObject(object_base.VersionedObject):
    OBJ_SERIAL_NAMESPACE = 'esi_leap_object'
    OBJ_PROJECT_NAMESPACE = 'esi_leap'

    fields = {
        'created_at': object_fields.DateTimeField(nullable=True),
        'updated_at': object_fields.DateTimeField(nullable=True),
    }

    @staticmethod
    def _from_db_object(context, obj, db_obj):
        for key in obj.fields:
            setattr(obj, key, db_obj[key])
            obj.obj_reset_changes()
        obj._context = context
        return obj

    @classmethod
    def _from_db_object_list(cls, context, db_objs):
        return [cls._from_db_object(context, cls(), db_obj)
                for db_obj in db_objs]

    def to_dict(self):
        return dict((k, getattr(self, k))
                    for k in self.fields
                    if self.obj_attr_is_set(k))
