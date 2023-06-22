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
import pecan
from pecan import rest
import wsme
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from esi_leap.api.controllers import base
from esi_leap.api.controllers import types
from esi_leap.api.controllers.v1 import utils
from esi_leap.common import exception
from esi_leap.common import keystone
import esi_leap.conf
from esi_leap.objects import event as event_obj
from esi_leap.resource_objects import get_resource_object

CONF = esi_leap.conf.CONF


class Event(base.ESILEAPBase):

    id = wsme.wsattr(int, readonly=True)
    event_type = wsme.wsattr(wtypes.text, readonly=True)
    event_time = wsme.wsattr(datetime.datetime, readonly=True)
    object_type = wsme.wsattr(wtypes.text, readonly=True)
    object_uuid = wsme.wsattr(wtypes.text, readonly=True)
    resource_type = wsme.wsattr(wtypes.text, readonly=True)
    resource_uuid = wsme.wsattr(wtypes.text, readonly=True)
    lessee_id = wsme.wsattr(wtypes.text, readonly=True)
    owner_id = wsme.wsattr(wtypes.text, readonly=True)

    def __init__(self, **kwargs):

        self.fields = event_obj.Event.fields
        for field in self.fields:
            setattr(self, field, kwargs.get(field, wtypes.Unset))


class EventCollection(types.Collection):
    events = [Event]

    def __init__(self, **kwargs):
        self._type = 'events'


class EventsController(rest.RestController):

    @wsme_pecan.wsexpose(EventCollection, int, wtypes.text,
                         datetime.datetime, wtypes.text, wtypes.text,
                         wtypes.text, wtypes.text)
    def get_all(self, last_event_id=None, lessee_or_owner_id=None,
                last_event_time=None, event_type=None,
                resource_type=None, resource_uuid=None):
        request = pecan.request.context
        cdict = request.to_policy_values()

        try:
            utils.policy_authorize('esi_leap:offer:offer_admin', cdict, cdict)
        except exception.HTTPForbidden:
            lessee_or_owner_id = cdict['project_id']

        if lessee_or_owner_id is not None:
            lessee_or_owner_id = keystone.get_project_uuid_from_ident(
                lessee_or_owner_id)

        if resource_uuid is not None:
            if resource_type is None:
                resource_type = CONF.api.default_resource_type
            resource = get_resource_object(resource_type, resource_uuid)
            resource_uuid = resource.get_uuid()

        filters = {
            'last_event_id': last_event_id,
            'last_event_time': last_event_time,
            'lessee_or_owner_id': lessee_or_owner_id,
            'event_type': event_type,
            'resource_type': resource_type,
            'resource_uuid': resource_uuid,
        }

        # unpack iterator to tuple so we can use 'del'
        for k, v in tuple(filters.items()):
            if v is None:
                del filters[k]

        events = event_obj.Event.get_all(filters, request)
        event_collection = EventCollection()
        event_collection.events = []
        for event in events:
            e = Event(id=event.id,
                      event_type=event.event_type,
                      event_time=event.event_time,
                      object_type=event.object_type,
                      object_uuid=event.object_uuid,
                      resource_type=event.resource_type,
                      resource_uuid=event.resource_uuid,
                      lessee_id=event.lessee_id,
                      owner_id=event.owner_id)
            event_collection.events.append(e)

        return event_collection
