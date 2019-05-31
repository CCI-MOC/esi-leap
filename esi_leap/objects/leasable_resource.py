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
from esi_leap.resource_objects import resource_object_factory as ro_factory


@versioned_objects_base.VersionedObjectRegistry.register
class LeasableResource(base.ESILEAPObject):
    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.IntegerField(),
        'resource_type': fields.StringField(),
        'resource_uuid': fields.StringField(),
        'expiration_date': fields.DateTimeField(nullable=True),
        'request_uuid': fields.UUIDField(nullable=True),
        'lease_expiration_date': fields.DateTimeField(nullable=True),
    }

    @classmethod
    def get(cls, context, resource_type, resource_uuid):
        db_resource = cls.dbapi.leasable_resource_get(
            context, resource_type, resource_uuid)
        return cls._from_db_object(context, cls(), db_resource)

    @classmethod
    def get_all(cls, context):
        db_resources = cls.dbapi.leasable_resource_get_all(context)
        return cls._from_db_object_list(context, db_resources)

    @classmethod
    def get_all_by_project_id(cls, context, project_id):
        db_resources = cls.dbapi.leasable_resource_get_all_by_project_id(
            context, project_id)
        return cls._from_db_object_list(context, db_resources)

    @classmethod
    def get_all_by_request_project_id(cls, context, project_id):
        db_resources = cls.dbapi. \
            leasable_resource_get_all_by_request_project_id(
                context, project_id)
        return cls._from_db_object_list(context, db_resources)

    @classmethod
    def get_all_by_request_uuid(cls, context, request_uuid):
        db_resources = cls.dbapi.leasable_resource_get_all_by_request_uuid(
            context, request_uuid)
        return cls._from_db_object_list(context, db_resources)

    @classmethod
    def get_available(cls, context):
        db_resources = cls.dbapi.leasable_resource_get_available(context)
        return cls._from_db_object_list(context, db_resources)

    @classmethod
    def get_leased(cls, context):
        db_resources = cls.dbapi.leasable_resource_get_leased(context)
        return cls._from_db_object_list(context, db_resources)

    def create(self, context=None):
        updates = self.obj_get_changes()
        db_resource = self.dbapi.leasable_resource_create(context, updates)
        self._from_db_object(context, self, db_resource)

    def destroy(self, context=None):
        self.unassign(context)
        self.dbapi.leasable_resource_destroy(
            context, self.resource_type, self.resource_uuid)
        self.obj_reset_changes()

    def save(self, context=None):
        updates = self.obj_get_changes()
        db_resource = self.dbapi.leasable_resource_update(
            context, self.resource_type, self.resource_uuid, updates)
        self._from_db_object(context, self, db_resource)

    def resource_object(self):
        return ro_factory.ResourceObjectFactory.get_resource_object(
            self.resource_type, self.resource_uuid)

    def is_available(self):
        return (self.request_uuid is None and
                self.resource_object().get_project_id() is None)

    def assign(self, context, request, expiration_date):
        self.request_uuid = request.uuid
        self.lease_expiration_date = expiration_date
        self.save(context)
        self.resource_object().set_project_id(request.project_id)

    def unassign(self, context):
        self.request_uuid = None
        self.lease_expiration_date = None
        self.save(context)
        self.resource_object().set_project_id(None)
