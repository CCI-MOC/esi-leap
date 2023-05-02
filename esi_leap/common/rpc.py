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
#    under the License.fic language governing permissions and limitations
#    under the License.

from esi_leap.common import exception
from esi_leap.conf import CONF
from oslo_context import context as ctx
import oslo_messaging as messaging
from osprofiler import profiler

NOTIFICATION_TRANSPORT = None
VERSIONED_NOTIFIER = None

ALLOWED_EXMODS = [
    exception.__name__,
]


def init(conf):
    global NOTIFICATION_TRANSPORT
    global VERSIONED_NOTIFIER
    NOTIFICATION_TRANSPORT = messaging.get_notification_transport(
        conf,
        allowed_remote_exmods=ALLOWED_EXMODS)

    serializer = RequestContextSerializer(messaging.JsonPayloadSerializer())

    if conf.notification.notification_level is None:

        VERSIONED_NOTIFIER = messaging.Notifier(NOTIFICATION_TRANSPORT,
                                                serializer=serializer,
                                                driver='noop')
    else:
        VERSIONED_NOTIFIER = messaging.Notifier(
            NOTIFICATION_TRANSPORT,
            serializer=serializer,
            topics=CONF.notification.versioned_notifications_topics)


def cleanup():
    global NOTIFICATION_TRANSPORT
    global VERSIONED_NOTIFIER
    assert NOTIFICATION_TRANSPORT is not None
    assert VERSIONED_NOTIFIER is not None
    NOTIFICATION_TRANSPORT.cleanup()
    NOTIFICATION_TRANSPORT = None
    VERSIONED_NOTIFIER = None


# RequestContextSerializer borrowed from Ironic
class RequestContextSerializer(messaging.Serializer):

    def __init__(self, base):
        self._base = base

    def serialize_entity(self, context, entity):
        if not self._base:
            return entity
        return self._base.serialize_entity(context, entity)

    def deserialize_entity(self, context, entity):
        if not self._base:
            return entity
        return self._base.deserialize_entity(context, entity)

    def serialize_context(self, context):
        _context = context.to_dict()
        prof = profiler.get()
        if prof:
            trace_info = {
                "hmac_key": prof.hmac_key,
                "base_id": prof.get_base_id(),
                "parent_id": prof.get_id()
            }
            _context.update({"trace_info": trace_info})
        return _context

    def deserialize_context(self, context):
        trace_info = context.pop("trace_info", None)
        if trace_info:
            profiler.init(**trace_info)
        return ctx.RequestContext.from_dict(context)


def get_versioned_notifier(publisher_id=None):
    assert VERSIONED_NOTIFIER is not None
    assert publisher_id is not None
    return VERSIONED_NOTIFIER.prepare(publisher_id=publisher_id)
