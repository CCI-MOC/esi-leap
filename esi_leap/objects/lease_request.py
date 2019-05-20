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

import datetime

from oslo_log import log as logging
from oslo_utils import timeutils
from oslo_versionedobjects import base as versioned_objects_base

from esi_leap.common import exception
from esi_leap.common import statuses
from esi_leap.db import api as dbapi
from esi_leap.objects import base
from esi_leap.objects import fields
from esi_leap.objects import leasable_resource


LOG = logging.getLogger(__name__)


@versioned_objects_base.VersionedObjectRegistry.register
class LeaseRequest(base.ESILEAPObject):
    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.IntegerField(),
        'uuid': fields.UUIDField(),
        'project_id': fields.StringField(),
        'name': fields.StringField(),
        'resource_properties': fields.FlexibleDictField(nullable=True),
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
        db_lease_requests = cls.dbapi.lease_request_get_all_by_project_id(
            context, project_id)
        return cls._from_db_object_list(context, db_lease_requests)

    @classmethod
    def get_all_by_status(cls, context, status):
        db_lease_requests = cls.dbapi.lease_request_get_all_by_status(
            context, status)
        return cls._from_db_object_list(context, db_lease_requests)

    def create(self, context=None):
        updates = self.obj_get_changes()
        db_lease_request = self.dbapi.lease_request_create(context, updates)
        self._from_db_object(context, self, db_lease_request)

    def destroy(self, context=None):
        self.dbapi.lease_request_destroy(context, self.uuid)
        self.obj_reset_changes()

    def save(self, context=None):
        updates = self.obj_get_changes()
        db_lease_request = self.dbapi.lease_request_update(
            context, self.uuid, updates)
        self._from_db_object(context, self, db_lease_request)

    # TODO: should probably be separated out somewhere else
    # TODO: this may need to be run as an admin user
    def fulfill(self, context):
        # TODO: we probably only want to fulfill one request at a time?

        if self.status != statuses.PENDING:
            raise exception.LeaseRequestWrongFulfillStatus(
                request_uuid=self.uuid, status=self.status)

        # check actual status
        actual_status = self._get_actual_status(context)
        if actual_status != self.status:
            raise exception.LeaseRequestIncorrectStatus(
                request_uuid=self.uuid,
                status=self.status,
                actual_status=actual_status
            )

        resources = []
        for resource_type, resource_properties in \
            self.resource_properties.items():
            # for now, only match resource_uuids
            # TODO: match based on resource properties
            resource_uuids = resource_properties.get('resource_uuids', [])
            for resource_uuid in resource_uuids:
                resource = leasable_resource.LeasableResource.get(
                    context, resource_type, resource_uuid)
                if resource is None or not resource.is_available():
                    LOG.info("%s %s is unavailable; lease cannot be fulfilled",
                             resource.resource_type, resource.resource_uuid)
                    return
                    resources.append(resource)

        # resources are all available, so claim them
        # TODO: should be done in a single transaction with above
        LOG.info("Resources are available; attempting to fulfill lease")
        fulfilled_date = timeutils.utcnow()
        expiration_date = fulfilled_date + datetime.timedelta(
            seconds=self.lease_time)
        for resource in resources:
            resource.assign(context, self, expiration_date)
            LOG.info("%s %s assigned to lease %s", resource.resource_type,
                     resource.resource_uuid, self.uuid)

        post_actual_status = self._get_actual_status(context)
        if post_actual_status in [statuses.DEGRADED, statuses.FULFILLED]:
            # at least some resources have been assigned, so start the timer
            self.fulfilled_date = fulfilled_date
            self.expiration_date = expiration_date
            self.status = post_actual_status
            self.save(context)
            LOG.info("Lease %s successfully fulfilled", self.uuid)
        else:
            raise exception.LeaseRequestUnfulfilled(request_uuid=self.uuid)

    def expire_or_cancel(self, context, target_status=statuses.EXPIRED):
        # if we call this method, assume that we always want to remove any
        # associated resources
        resources = leasable_resource.LeasableResource.get_all_by_request_uuid(
            context, self.uuid)

        # TODO: should be done in a single transaction
        for resource in resources:
            resource.unassign(context)
            LOG.info("%s %s removed from lease %s",
                     resource.resource_type, resource.resource_uuid, self.uuid)

        # check that there are no resources left
        post_resources = leasable_resource. \
            LeasableResource.get_all_by_request_uuid(
                context, self.uuid)

        if len(post_resources) > 0:
            raise exception.LeaseRequestUnexpired(
                request_uuid=self.uuid)

        self.status = target_status
        self.save(context)
        LOG.info("Lease %s successfully %s", self.uuid, target_status)

    def _get_expected_resource_count(self):
        # TODO: add resources from resource_properties
        # TODO: different resource types?
        count = 0
        for resource_type, resource_properties in \
            self.resource_properties.items():
            count += len(resource_properties.get('resource_uuids', []))
        return count

    def _get_actual_status(self, context=None):
        # check if lease request has any resources
        resources = leasable_resource.LeasableResource.get_all_by_request_uuid(
            context, self.uuid)

        if len(resources) > 0:
            # request has been at least partially fulfilled, and is not expired
            if self._get_expected_resources_count() == len(resources):
                return statuses.FULFILLED
            return statuses.DEGRADED
        else:
            # request is either pending or completed
            if self.cancel_date and self.cancel_date <= timeutils.utcnow():
                return statuses.CANCELLED
            elif self.expiration_date and \
                self.expiration_date <= timeutils.utcnow():
                return statuses.EXPIRED
            elif self.fulfilled_date is None:
                return statuses.PENDING
            else:
                # request is fulfilled but has no resources
                return statuses.DEGRADED
