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

from esi_leap.common import ironic
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

    def is_available(self):
        return (self.request_uuid is None and
                ironic.get_node_project_id(self.node_uuid) is None)

    def assign_node(self, context, request_uuid, expiration_date):
        self.request_uuid = request_uuid
        self.lease_expiration_date = expiration_date
        self.save(context)
        ironic.set_node_project_id(self.node_uuid, context.project_id)

    def unassign_node(self, context):
        self.request_uuid = None
        self.lease_expiration_date = None
        self.save(context)
        ironic.set_node_project_id(self.node_uuid, None)
