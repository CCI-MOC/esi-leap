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
        db_policies = cls.dbapi.policy_get_all_by_project_id(
            context, project_id)
        return cls._from_db_object_list(context, db_policies)

    def create(self, context=None):
        updates = self.obj_get_changes()
        db_policy = self.dbapi.policy_create(context, updates)
        self._from_db_object(context, self, db_policy)

    def destroy(self, context=None):
        self.dbapi.policy_destroy(context, self.uuid)
        self.obj_reset_changes()

    def save(self, context=None):
        updates = self.obj_get_changes()
        db_policy = self.dbapi.policy_update(context, self.uuid, updates)
        self._from_db_object(context, self, db_policy)
