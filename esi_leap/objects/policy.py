from oslo_utils import uuidutils
from oslo_versionedobjects import base as versioned_objects_base

from esi_leap.db import api as dbapi
from esi_leap.objects import base
from esi_leap.objects import fields


@versioned_objects_base.VersionedObjectRegistry.register
class Policy(base.ESILEAPObject):
    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.IntegerField(),
        'uuid': fields.UUIDField(),
        'project_id': fields.StringField(),
        'name': fields.StringField(),
        'max_time_for_lease': fields.IntegerField(default=0),
        'extendible': fields.BooleanField(default=False),
    }


    @classmethod
    def get(cls, context, policy_uuid):
        db_policy = cls.dbapi.policy_get(context, policy_uuid)
        return cls._from_db_object(context, cls(), db_policy)


    @classmethod
    def get_all(cls, context):
        db_policies = cls.dbapi.policy_get_all(context)
        return cls._from_db_object_list(context, db_policies)


    @classmethod
    def get_all_by_project_id(cls, context, project_id):
        db_policies = cls.dbapi.policy_get_all_by_project_id(context, project_id)
        return cls._from_db_object_list(context, db_policies)


    def create(self, context=None):
        updates = self.obj_get_changes()
        if 'uuid' not in updates:
            updates['uuid'] = uuidutils.generate_uuid()
            self.uuid = updates['uuid']

        db_policy = self.dbapi.policy_create(context, updates)
        self._from_db_object(context, self, db_policy)


    def destroy(self, context=None):
        self.dbapi.policy_destroy(context, self.uuid)
        self.obj_reset_changes()


    def save(self, context=None):
        updates = self.obj_get_changes()
        db_policy = self.dbapi.policy_update(context, self.uuid, updates)
        self._from_db_object(context, self, db_policy)
