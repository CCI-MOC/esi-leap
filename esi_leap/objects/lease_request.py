import datetime

from oslo_versionedobjects import base as versioned_objects_base

from esi_leap.common import exception
from esi_leap.common import ironic
from esi_leap.common import statuses
from esi_leap.db import api as dbapi
from esi_leap.objects import base
from esi_leap.objects import fields
from esi_leap.objects import policy_node


@versioned_objects_base.VersionedObjectRegistry.register
class LeaseRequest(base.ESILEAPObject):
    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.IntegerField(),
        'uuid': fields.UUIDField(),
        'project_id': fields.StringField(),
        'name': fields.StringField(),
        'node_properties': fields.FlexibleDictField(nullable=True),
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
        db_lease_requests = cls.dbapi.lease_request_get_all_by_project_id(
            context, project_id)
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
    def fulfill(self, context=None):
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

        # for now, only match node_uuids
        # TODO: match based on node properties
        node_uuids = self.node_properties.get('node_uuids', [])
        nodes = []
        for node_uuid in node_uuids:
            node = policy_node.PolicyNode.get(context, node_uuid)
            if node is None or node.request_uuid is not None or \
               ironic.get_node_project_id(node_uuid) is not None:
                raise exception.LeaseRequestNodeUnavailable(
                    request_uuid=self.uuid)
            nodes.append(node)

        # nodes are all available, so claim them
        # TODO: should be done in a single transaction
        fulfilled_date = datetime.datetime.utcnow()
        expiration_date = fulfilled_date + datetime.timedelta(
            seconds=self.lease_time)
        for node in nodes:
            node.request_uuid = self.uuid
            node.lease_expiration_date = expiration_date
            node.save(context)
            ironic.set_node_project_id(node.node_uuid, context.project_id)

        post_actual_status = self._get_actual_status(context)
        if post_actual_status in [statuses.DEGRADED, statuses.FULFILLED]:
            # at least some nodes have been assigned, so start the timer
            self.fulfilled_date = fulfilled_date
            self.expiration_date = expiration_date
            self.status = post_actual_status
            self.save(context)
        else:
            raise exception.LeaseRequestUnfulfilled(request_uuid=self.uuid)

    def expire(self, context=None):
        # if we call this method, assume that we always want to remove any
        # associated nodes
        nodes = policy_node.PolicyNode.get_all_by_request_uuid(
            context, self.uuid)

        # TODO: should be done in a single transaction
        for node in nodes:
            node.request_uuid = None
            node.lease_expiration_date = None
            node.save(context)
            ironic.set_node_project_id(node.node_uuid, None)

        # check that there are no nodes left
        post_nodes = policy_node.PolicyNode.get_all_by_request_uuid(
            context, self.uuid)

        if len(post_nodes) > 0:
            raise exception.LeaseRequestNodeUnexpired(
                request_uuid=self.uuid)

        self.status = statuses.EXPIRED
        self.save(context)

    def _get_expected_node_count(self):
        # TODO: add nodes from node_properties
        return len(self.node_properties.get('node_uuids', []))

    def _get_actual_status(self, context=None):
        # check if lease request has any nodes
        nodes = policy_node.PolicyNode.get_all_by_request_uuid(
            context, self.uuid)

        if len(nodes) > 0:
            # request has been at least partially fulfilled, and is not expired
            if self._get_expected_node_count() == len(nodes):
                return statuses.FULFILLED
            return statuses.DEGRADED
        else:
            # request is either pending or completed
            if self.cancel_date is not None:
                return statuses.CANCELLED
            elif self.expiration_date is not None:
                return statuses.EXPIRED
            elif self.fulfilled_date is None:
                return statuses.PENDING
            else:
                # request is fulfilled but has no nodes
                return statuses.DEGRADED
