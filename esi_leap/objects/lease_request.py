from oslo_utils import uuidutils
from oslo_versionedobjects import base as versioned_objects_base

from esi_leap.db import api as dbapi
from esi_leap.objects import base
from esi_leap.objects import fields


@versioned_objects_base.VersionedObjectRegistry.register
class LeaseRequest(base.ESILEAPObject):
    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.IntegerField(),
        'uuid': fields.UUIDField(),
        'project_id': fields.StringField(),
        'name': fields.StringField(),
        'node_properties': fields.DictOfStringsField(nullable=True),
        'min_nodes': fields.IntegerField(default=0),
        'max_nodes': fields.IntegerField(default=0),
        'lease_time': fields.IntegerField(default=0),
        'status': fields.StringField(),
        'cancel_date': fields.DateTimeField(nullable=True),
        'fulfilled_date': fields.DateTimeField(nullable=True),
        'expiration_date': fields.DateTimeField(nullable=True),
    }


    @classmethod
    def get(cls, context, request_uuid):
        db_lease_request = cls.dbapi.lease_request_get(context, request_uuid)
        return cls._from_db_object(context, cls(), db_lease_request)


    @classmethod
    def get_all(cls, context):
        db_lease_requests = cls.dbapi.lease_request_get_all(context)
        return cls._from_db_object_list(context, db_lease_requests)


    @classmethod
    def get_all_by_project_id(cls, context, project_id):
        db_lease_requests = cls.dbapi.lease_request_get_all_by_project_id(context, project_id)
        return cls._from_db_object_list(context, db_lease_requests)


    def create(self, context=None):
        updates = self.obj_get_changes()

        if 'uuid' not in updates:
            updates['uuid'] = uuidutils.generate_uuid()
            self.uuid = updates['uuid']

        db_lease_request = self.dbapi.lease_request_create(context, updates)
        self._from_db_object(context, self, db_lease_request)


    def destroy(self, context=None):
        self.dbapi.lease_request_destroy(context, self.uuid)
        self.obj_reset_changes()


    def save(self, context=None):
        updates = self.obj_get_changes()
        db_lease_request = self.dbapi.lease_request_update(context, self.uuid, updates)
        self._from_db_object(context, self, db_lease_request)
