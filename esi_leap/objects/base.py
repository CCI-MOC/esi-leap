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
