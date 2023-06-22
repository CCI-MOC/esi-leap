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

import contextlib

from oslo_config import cfg
from oslo_log import log
from oslo_messaging import exceptions as oslo_msg_exc
from oslo_utils import excutils
from oslo_versionedobjects import exception as oslo_vo_exc

from esi_leap.common import exception
from esi_leap.common.i18n import _
from esi_leap.objects import fields
from esi_leap.objects import notification

LOG = log.getLogger(__name__)
CONF = cfg.CONF


def _emit_notification(context, obj, action, level, status,
                       crud_notify_obj, **kwargs):
    """Helper for emitting notifications.

    :param context: request context.
    :param obj: resource rpc object.
    :param action: Action string to go in the EventType.
    :param level: Notification level. One of
                  `esi_leap.objects.fields.NotificationLevel.ALL`
    :param status: Status to go in the EventType. One of
                   `esi_leap.objects.fields.NotificationStatus.ALL`
    :param kwargs: kwargs to use when creating the notification payload.
    """
    resource = obj.__class__.__name__.lower()
    extra_args = kwargs
    exception_values = {}
    exception_message = None
    try:
        try:
            if resource not in crud_notify_obj:
                notification_name = payload_name = _("is not defined")
                raise KeyError(_("Unsupported resource: %s") % resource)
            else:
                notification_method, payload_method = crud_notify_obj[resource]

            notification_name = notification_method.__name__
            payload_name = payload_method.__name__
        finally:
            # Prepare our exception message just in case
            exception_values = {"resource": resource,
                                "uuid": obj.uuid,
                                "action": action,
                                "status": status,
                                "level": level,
                                "notification_method": notification_name,
                                "payload_method": payload_name}
            exception_message = (_("Failed to send esi_leap.%(resource)s."
                                   "%(action)s.%(status)s notification for "
                                   "%(resource)s %(uuid)s with level "
                                   "%(level)s, notification method "
                                   "%(notification_method)s, payload method "
                                   "%(payload_method)s, error %(error)s"))
        payload = payload_method(obj, **extra_args)
        event_type = "esi_leap.%s.%s.%s" % (resource, action, status)
        notification_method(
            publisher=notification.NotificationPublisher(
                service='esi-leap-manager', host=CONF.host),
            event_type=notification.EventType(
                object=resource, action=action, status=status),
            level=level,
            payload=payload).emit(context)
        LOG.info("Emit esi_leap notification: host is %s "
                 "event is %s ,"
                 "level is %s ,"
                 "notification method is %s",
                 CONF.host, event_type,
                 level, notification_method)
    except (exception.NotificationSchemaObjectError,
            exception.NotificationSchemaKeyError,
            exception.NotificationPayloadError,
            oslo_msg_exc.MessageDeliveryFailure,
            oslo_vo_exc.VersionedObjectsException) as e:
        exception_values['error'] = e
        LOG.warning(exception_message, exception_values)
        LOG.exception(e.msg_fmt)

    except Exception as e:
        exception_values['error'] = e
        LOG.exception(exception_message, exception_values)


def emit_start_notification(context, obj, action, crud_notify_obj, **kwargs):
    """Helper for emitting API 'start' notifications.

    :param context: request context.
    :param obj: resource rpc object.
    :param action: Action string to go in the EventType.
    :param kwargs: kwargs to use when creating the notification payload.
    """
    _emit_notification(context, obj, action,
                       fields.NotificationLevel.INFO,
                       fields.NotificationStatus.START,
                       crud_notify_obj,
                       **kwargs)


@contextlib.contextmanager
def handle_error_notification(context, obj, action, crud_notify_obj, **kwargs):
    """Context manager to handle any error notifications.

    :param context: request context.
    :param obj: resource rpc object.
    :param action: Action string to go in the EventType.
    :param kwargs: kwargs to use when creating the notification payload.
    """
    try:
        yield
    except Exception:
        with excutils.save_and_reraise_exception():
            _emit_notification(context, obj, action,
                               fields.NotificationLevel.ERROR,
                               fields.NotificationStatus.ERROR,
                               crud_notify_obj,
                               **kwargs)


def emit_end_notification(context, obj, action, crud_notify_obj, **kwargs):
    """Helper for emitting API 'end' notifications.

    :param context: request context.
    :param obj: resource rpc object.
    :param action: Action string to go in the EventType.
    :param kwargs: kwargs to use when creating the notification payload.
    """
    _emit_notification(context, obj, action,
                       fields.NotificationLevel.INFO,
                       fields.NotificationStatus.END,
                       crud_notify_obj,
                       **kwargs)
