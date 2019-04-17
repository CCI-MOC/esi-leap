import datetime

from oslo_versionedobjects import base as versioned_objects_base

from esi_leap.common import exception
from esi_leap.common import ironic
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
        db_lease_requests = cls.dbapi.lease_request_get_all_by_project_id(context, project_id)
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
        db_lease_request = self.dbapi.lease_request_update(context, self.uuid, updates)
        self._from_db_object(context, self, db_lease_request)


    # TODO: should probably be separated out somewhere else
    # TODO: this may need to be run as an admin user
    def fulfill(self, context=None):
        # TODO: we probably only want to fulfill one request at a time?

        if self.status != 'pending':
            raise exception.LeaseRequestWrongFulfillStatus(request_uuid=self.uuid, status=self.status)

        # for now, only match node_uuids
        # TODO: match based on node properties
        node_uuids = self.node_properties.get('node_uuids', [])
        nodes = []
        for node_uuid in node_uuids:
            node = policy_node.PolicyNode.get(context, node_uuid)
            if node == None or node.request_uuid != None:
                raise exception.LeaseRequestNodeUnavailable(request_uuid=self.uuid)
            # TODO: also check ironic node to see if project_id is set
            nodes.append(node)

        # nodes are all available, so claim them
        # TODO: should be done in a single transaction
        fulfilled_date = datetime.datetime.utcnow()
        expiration_date = fulfilled_date + datetime.timedelta(seconds=self.lease_time)
        for node in nodes:
            node.request_uuid = self.uuid
            node.lease_expiration_date = expiration_date
            node.save(context)
            ironic.set_node_project_id(node.node_uuid, context.project_id)

        # TODO: verify claim succeeded

        self.fulfilled_date = fulfilled_date
        self.expiration_date = expiration_date
        self.status = 'fulfilled'
        self.save(context)
