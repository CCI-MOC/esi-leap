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

from esi_leap.common import exception
from esi_leap.common import notification_utils as notify
from esi_leap.common import statuses
from esi_leap.common import utils
from esi_leap.db import api as dbapi
from esi_leap.objects import base
from esi_leap.objects import fields
from esi_leap.objects import notification
from esi_leap.objects import offer as offer_obj
from esi_leap.resource_objects import get_resource_object

from oslo_config import cfg
from oslo_log import log as logging
from oslo_versionedobjects import base as versioned_objects_base

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


@versioned_objects_base.VersionedObjectRegistry.register
class LeaseCRUDNotification(notification.NotificationBase):
    """Notification emitted when a lease is created or deleted."""

    fields = {
        'payload': fields.ObjectField('LeaseCRUDPayload')
    }


@versioned_objects_base.VersionedObjectRegistry.register
class LeaseCRUDPayload(notification.NotificationPayloadBase):
    """Payload schema for when a lease is created or deleted."""
    # Version 1.0: Initial version
    VERSION = '1.0'

    SCHEMA = {
        'id': ('lease', 'id'),
        'name': ('lease', 'name'),
        'uuid': ('lease', 'uuid'),
        'project_id': ('lease', 'project_id'),
        'owner_id': ('lease', 'owner_id'),
        'resource_type': ('lease', 'resource_type'),
        'resource_uuid': ('lease', 'resource_uuid'),
        'start_time': ('lease', 'start_time'),
        'end_time': ('lease', 'end_time'),
        'fulfill_time': ('lease', 'fulfill_time'),
        'expire_time': ('lease', 'expire_time'),
        'status': ('lease', 'status'),
        'properties': ('lease', 'properties'),
        'purpose': ('lease', 'purpose'),
        'offer_uuid': ('lease', 'offer_uuid'),
        'parent_lease_uuid': ('lease', 'parent_lease_uuid'),
        'node_name': ('node', 'node_name'),
        'node_uuid': ('node', '_uuid'),
        'node_provision_state': ('node', 'node_provision_state'),
        'node_power_state': ('node', 'node_power_state'),
        'node_properties': ('node', 'node_properties'),
    }

    fields = {
        'id': fields.IntegerField(),
        'name': fields.StringField(nullable=True),
        'uuid': fields.UUIDField(),
        'project_id': fields.StringField(),
        'owner_id': fields.StringField(),
        'purpose': fields.StringField(nullable=True),
        'resource_type': fields.StringField(),
        'resource_uuid': fields.StringField(),
        'start_time': fields.DateTimeField(nullable=True),
        'end_time': fields.DateTimeField(nullable=True),
        'fulfill_time': fields.DateTimeField(nullable=True),
        'expire_time': fields.DateTimeField(nullable=True),
        'status': fields.StringField(),
        'properties': fields.FlexibleDictField(nullable=True),
        'offer_uuid': fields.UUIDField(nullable=True),
        'parent_lease_uuid': fields.UUIDField(nullable=True),
        'node_name': fields.StringField(nullable=True),
        'node_uuid': fields.UUIDField(),
        'node_provision_state': fields.StringField(),
        'node_power_state': fields.StringField(),
        'node_properties': fields.FlexibleDictField(nullable=True),
    }

    def __init__(self, lease, node):
        super(LeaseCRUDPayload, self).__init__()

        setattr(node, 'node_name', node.get_name())
        setattr(node, 'node_provision_state', node.get_node_provision_state())
        setattr(node, 'node_power_state', node.get_node_power_state())
        node_config = node.get_config().copy()
        node_config.pop('lease_uuid', None)
        setattr(node, 'node_properties', node_config)

        self.populate_schema(lease=lease, node=node)

    def get_event_dict(self, event_type):
        event_dict = super().get_event_dict(event_type)
        event_dict.update({
            'object_type': 'lease',
            'object_uuid': self.uuid,
            'resource_type': self.resource_type,
            'resource_uuid': self.resource_uuid,
            'lessee_id': self.project_id,
            'owner_id': self.owner_id,
        })
        return event_dict


CRUD_NOTIFY_OBJ = {
    'lease': (LeaseCRUDNotification, LeaseCRUDPayload),
}


@versioned_objects_base.VersionedObjectRegistry.register
class Lease(base.ESILEAPObject):
    dbapi = dbapi.get_instance()

    fields = {
        'id': fields.IntegerField(),
        'name': fields.StringField(nullable=True),
        'uuid': fields.UUIDField(),
        'project_id': fields.StringField(),
        'owner_id': fields.StringField(),
        'purpose': fields.StringField(nullable=True),
        'resource_type': fields.StringField(),
        'resource_uuid': fields.StringField(),
        'start_time': fields.DateTimeField(nullable=True),
        'end_time': fields.DateTimeField(nullable=True),
        'fulfill_time': fields.DateTimeField(nullable=True),
        'expire_time': fields.DateTimeField(nullable=True),
        'status': fields.StringField(),
        'properties': fields.FlexibleDictField(nullable=True),
        'offer_uuid': fields.UUIDField(nullable=True),
        'parent_lease_uuid': fields.UUIDField(nullable=True),
    }

    @classmethod
    def get(cls, lease_uuid, context=None):
        db_lease = cls.dbapi.lease_get_by_uuid(lease_uuid)
        if db_lease:
            return cls._from_db_object(context, cls(), db_lease)

    @classmethod
    def get_all(cls, filters, context=None):
        db_leases = cls.dbapi.lease_get_all(filters)
        return cls._from_db_object_list(context, db_leases)

    def create(self, context=None):
        updates = self.obj_get_changes()

        with utils.lock(utils.get_resource_lock_name(updates['resource_type'],
                                                     updates['resource_uuid']),
                        external=True):
            if updates['start_time'] >= updates['end_time']:
                raise exception.InvalidTimeRange(
                    resource='lease',
                    start_time=str(updates['start_time']),
                    end_time=str(updates['end_time'])
                    )

            # check availability
            if 'offer_uuid' in updates:
                # lease is being created from an offer
                related_offer = offer_obj.Offer.get(updates['offer_uuid'])

                if related_offer.status != statuses.AVAILABLE:
                    raise exception.OfferNotAvailable(
                        offer_uuid=related_offer.uuid,
                        status=related_offer.status)

                related_offer.verify_availability(updates['start_time'],
                                                  updates['end_time'])
            elif 'parent_lease_uuid' in updates:
                # lease is a child of an existing lease
                parent_lease = Lease.get(updates['parent_lease_uuid'])

                if parent_lease.status != statuses.ACTIVE:
                    raise exception.LeaseNotActive(
                        updates['parent_lease_uuid'])

                parent_lease.verify_child_availability(updates['start_time'],
                                                       updates['end_time'])
            else:
                ro = get_resource_object(updates['resource_type'],
                                         updates['resource_uuid'])
                ro.verify_availability(updates['start_time'],
                                       updates['end_time'])

            db_lease = self.dbapi.lease_create(updates)
            self._from_db_object(context, self, db_lease)

    def cancel(self, context=None):
        leases = Lease.get_all(
            {'parent_lease_uuid': self.uuid,
             'status': statuses.LEASE_CAN_DELETE},
            None)
        for lease in leases:
            lease.cancel()
        offers = offer_obj.Offer.get_all(
            {'parent_lease_uuid': self.uuid,
             'status': statuses.OFFER_CAN_DELETE},
            None)
        for offer in offers:
            offer.cancel()

        with utils.lock(utils.get_resource_lock_name(self.resource_type,
                                                     self.resource_uuid),
                        external=True):
            LOG.info('Deleting lease %s', self.uuid)
            try:
                resource = self.resource_object()
                self.deactivate(context, resource)
                self.status = statuses.DELETED
                self.expire_time = datetime.datetime.now()

            except Exception as e:
                LOG.info('Error canceling lease: %s: %s' %
                         (type(e).__name__, e))
                LOG.info('Setting lease status to WAIT')
                self.status = statuses.WAIT_CANCEL
            self.save(context)

    def destroy(self):
        self.dbapi.lease_destroy(self.uuid)
        self.obj_reset_changes()

    def save(self, context=None):
        updates = self.obj_get_changes()
        db_lease = self.dbapi.lease_update(
            self.uuid, updates)
        self._from_db_object(context, self, db_lease)

    def fulfill(self, context=None):
        with utils.lock(utils.get_resource_lock_name(self.resource_type,
                                                     self.resource_uuid),
                        external=True):
            LOG.info('Fulfilling lease %s', self.uuid)
            try:
                resource = self.resource_object()
                notify.emit_start_notification(context, self,
                                               'fulfill',
                                               CRUD_NOTIFY_OBJ,
                                               node=resource)
                with notify.handle_error_notification(context,
                                                      self,
                                                      'fulfill',
                                                      CRUD_NOTIFY_OBJ,
                                                      node=resource):
                    resource.set_lease(self)

                notify.emit_end_notification(context, self,
                                             'fulfill',
                                             CRUD_NOTIFY_OBJ,
                                             node=resource)

                self.status = statuses.ACTIVE
                self.fulfill_time = datetime.datetime.now()

            except Exception as e:
                LOG.info('Error fulfilling lease: %s: %s' %
                         (type(e).__name__, e))
                LOG.info('Setting lease status to WAIT')
                self.status = statuses.WAIT_FULFILL
            self.save(context)

    def expire(self, context=None):
        leases = Lease.get_all(
            {'parent_lease_uuid': self.uuid,
             'status': statuses.LEASE_CAN_DELETE},
            None)
        for lease in leases:
            lease.expire(context)
        offers = offer_obj.Offer.get_all(
            {'parent_lease_uuid': self.uuid,
             'status': statuses.OFFER_CAN_DELETE},
            None)
        for offer in offers:
            offer.expire(context)

        with utils.lock(utils.get_resource_lock_name(self.resource_type,
                                                     self.resource_uuid),
                        external=True):
            LOG.info('Expiring lease %s', self.uuid)
            try:
                # expire lease
                resource = self.resource_object()
                self.deactivate(context, resource)
                self.status = statuses.EXPIRED
                self.expire_time = datetime.datetime.now()

            except Exception as e:
                LOG.info('Error expiring lease: %s: %s' %
                         (type(e).__name__, e))
                LOG.info('Setting lease status to WAIT')
                self.status = statuses.WAIT_EXPIRE
            self.save(context)

    def resource_object(self):
        return get_resource_object(self.resource_type, self.resource_uuid)

    def verify_child_availability(self, start_time, end_time):
        return self.dbapi.lease_verify_child_availability(
            self, start_time, end_time)

    def deactivate(self, context, resource):
        notify.emit_start_notification(context, self,
                                       'delete', CRUD_NOTIFY_OBJ,
                                       node=resource)

        with notify.handle_error_notification(context,
                                              self,
                                              'delete',
                                              CRUD_NOTIFY_OBJ,
                                              node=resource):
            if resource.get_lease_uuid() == self.uuid:
                resource.remove_lease(self)

                if self.parent_lease_uuid is not None:
                    parent_lease = Lease.get(self.parent_lease_uuid)
                    resource.set_lease(parent_lease)

        notify.emit_end_notification(context, self,
                                     'delete', CRUD_NOTIFY_OBJ,
                                     node=resource)
