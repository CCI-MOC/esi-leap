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

from datetime import datetime

from oslo_config import cfg
from oslo_versionedobjects import base as versioned_objects_base

from esi_leap.common import exception
from esi_leap.common import rpc
from esi_leap.objects import base
from esi_leap.objects import event as event_obj
from esi_leap.objects import fields
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


CONF = cfg.CONF

# Notification object borrowed from Ironic

# Definition of notification levels in increasing order of severity
NOTIFY_LEVELS = {
    fields.NotificationLevel.DEBUG: 0,
    fields.NotificationLevel.INFO: 1,
    fields.NotificationLevel.WARNING: 2,
    fields.NotificationLevel.ERROR: 3,
    fields.NotificationLevel.CRITICAL: 4
}


@versioned_objects_base.VersionedObjectRegistry.register
class EventType(base.ESILEAPObject):
    """Defines the event_type to be sent on the wire.

    An EventType must specify the object being acted on, a string describing
    the action being taken on the notification, and the status of the action.
    """
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'object': fields.StringField(nullable=False),
        'action': fields.StringField(nullable=False),
        'status': fields.NotificationStatusField()
    }

    def to_event_type_field(self):
        """Constructs string for event_type to be sent on the wire.

           The string is in the format: esi_leap.<object>.<action>.<status>

           :raises: ValueError if self.status is not one of
                    :class:`fields.NotificationStatusField`
           :returns: event_type string
        """
        parts = ['esi_leap', self.object, self.action, self.status]
        return '.'.join(parts)


class NotificationBase(base.ESILEAPObject):
    """Base class for versioned notifications.

    Subclasses must define the "payload" field, which must be a subclass of
    NotificationPayloadBase.
    """
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'level': fields.NotificationLevelField(),
        'event_type': fields.ObjectField('EventType'),
        'publisher': fields.ObjectField('NotificationPublisher')
    }

    def _should_notify(self):
        """Determine whether the notification should be sent.

        A notification is sent when the level of the notification is
        greater than or equal to the level specified in the
        configuration, in the increasing order of DEBUG, INFO, WARNING,
        ERROR, CRITICAL.

        :return: True if notification should be sent, False otherwise.
        """
        if CONF.notification.notification_level is None:
            return False
        return (NOTIFY_LEVELS[self.level] >=
                NOTIFY_LEVELS[CONF.notification.notification_level])

    def emit(self, context):
        """Send the notification.

           :raises: NotificationPayloadError
           :raises: oslo_versionedobjects.exceptions.MessageDeliveryFailure
        """
        if not self._should_notify():
            return
        if not self.payload.populated:
            raise exception.NotificationPayloadError(
                class_name=self.__class__.__name__)

        self.payload.obj_reset_changes()
        event_type = self.event_type.to_event_type_field()
        publisher_id = '%s.%s' % (self.publisher.service, self.publisher.host)
        payload = self.payload.obj_to_primitive()
        notifier = rpc.get_versioned_notifier(publisher_id)

        notify = getattr(notifier, self.level)
        notify(context, event_type=event_type, payload=payload)

        event_dict = self.payload.get_event_dict(event_type)
        event = event_obj.Event(**event_dict)
        event.create()


class NotificationPayloadBase(base.ESILEAPObject):
    """Base class for the payload of versioned notifications."""

    SCHEMA = {}
    # Version 1.0: Initial version
    VERSION = '1.0'

    def __init__(self, *args, **kwargs):
        super(NotificationPayloadBase, self).__init__(*args, **kwargs)
        # If SCHEMA is empty, the payload is already populated
        self.populated = not self.SCHEMA

    def populate_schema(self, **kwargs):
        """Populate the object based on the SCHEMA and the source objects

        :param kwargs: A dict contains the source object and the keys defined
                       in the SCHEMA
        :raises: NotificationSchemaObjectError
        :raises: NotificationSchemaKeyError
        """
        for key, (obj, field) in self.SCHEMA.items():
            try:
                source = kwargs[obj]
            except KeyError:
                raise exception.NotificationSchemaObjectError(obj=obj,
                                                              source=kwargs)
            try:
                setattr(self, key, getattr(source, field))
            except NotImplementedError:
                # The object is missing (a value for) field. Oslo try to load
                # value via obj_load_attr() method which is not implemented.
                # If this field is nullable in this payload, set its payload
                # value to None.
                field_obj = self.fields.get(key)
                if field_obj is not None and getattr(field_obj, 'nullable',
                                                     False):
                    setattr(self, key, None)
                    continue
                raise exception.NotificationSchemaKeyError(obj=obj,
                                                           field=field,
                                                           key=key)
            except Exception:
                raise exception.NotificationSchemaKeyError(obj=obj,
                                                           field=field,
                                                           key=key)
        self.populated = True

    def get_event_dict(self, event_type):
        return {
            'event_type': event_type,
            'event_time': datetime.now(),
        }


@versioned_objects_base.VersionedObjectRegistry.register
class NotificationPublisher(base.ESILEAPObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    fields = {
        'service': fields.StringField(nullable=False),
        'host': fields.StringField(nullable=False)
    }
