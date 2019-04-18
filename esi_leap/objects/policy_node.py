from oslo_versionedobjects import base as versioned_objects_base

from esi_leap.db import api as dbapi
from esi_leap.objects import base
from esi_leap.objects import fields


@versioned_objects_base.VersionedObjectRegistry.register
class PolicyNode(base.ESILEAPObject):
    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.IntegerField(),
        'node_uuid': fields.UUIDField(),
        'policy_uuid': fields.UUIDField(),
        'expiration_date': fields.DateTimeField(nullable=True),
        'request_uuid': fields.UUIDField(nullable=True),
        'lease_expiration_date': fields.DateTimeField(nullable=True),
    }

    @classmethod
    def get(cls, context, node_uuid):
        db_policy_node = cls.dbapi.policy_node_get(context, node_uuid)
        return cls._from_db_object(context, cls(), db_policy_node)

    @classmethod
    def get_all(cls, context):
        db_policy_nodes = cls.dbapi.policy_node_get_all(context)
        return cls._from_db_object_list(context, db_policy_nodes)

    @classmethod
    def get_all_by_project_id(cls, context, project_id):
        db_policy_nodes = cls.dbapi.policy_node_get_all_by_project_id(
            context, project_id)
        return cls._from_db_object_list(context, db_policy_nodes)

    @classmethod
    def get_all_by_request_project_id(cls, context, project_id):
        db_policy_nodes = cls.dbapi.policy_node_get_all_by_request_project_id(
            context, project_id)
        return cls._from_db_object_list(context, db_policy_nodes)

    @classmethod
    def get_all_by_policy_uuid(cls, context, policy_uuid):
        db_policy_nodes = cls.dbapi.policy_node_get_all_by_policy_uuid(
            context, policy_uuid)
        return cls._from_db_object_list(context, db_policy_nodes)

    @classmethod
    def get_all_by_request_uuid(cls, context, request_uuid):
        db_policy_nodes = cls.dbapi.policy_node_get_all_by_request_uuid(
            context, request_uuid)
        return cls._from_db_object_list(context, db_policy_nodes)

    @classmethod
    def get_available(cls, context):
        db_policy_nodes = cls.dbapi.policy_node_get_available(context)
        return cls._from_db_object_list(context, db_policy_nodes)

    def create(self, context=None):
        updates = self.obj_get_changes()
        db_policy_node = self.dbapi.policy_node_create(context, updates)
        self._from_db_object(context, self, db_policy_node)

    def destroy(self, context=None):
        self.dbapi.policy_node_destroy(context, self.node_uuid)
        self.obj_reset_changes()

    def save(self, context=None):
        updates = self.obj_get_changes()
        db_policy_node = self.dbapi.policy_node_update(
            context, self.node_uuid, updates)
        self._from_db_object(context, self, db_policy_node)
