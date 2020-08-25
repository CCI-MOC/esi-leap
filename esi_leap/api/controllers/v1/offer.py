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
from oslo_utils import uuidutils
import pecan
from pecan import rest
import wsme
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from esi_leap.api.controllers import base
from esi_leap.api.controllers import types
from esi_leap.api.controllers.v1 import utils
from esi_leap.common import exception
from esi_leap.common import policy
from esi_leap.common import statuses
from esi_leap.objects import offer


class Offer(base.ESILEAPBase):

    name = wsme.wsattr(wtypes.text)
    uuid = wsme.wsattr(wtypes.text, readonly=True)
    project_id = wsme.wsattr(wtypes.text, readonly=True)
    resource_type = wsme.wsattr(wtypes.text, mandatory=True)
    resource_uuid = wsme.wsattr(wtypes.text, mandatory=True)
    start_time = wsme.wsattr(datetime.datetime)
    end_time = wsme.wsattr(datetime.datetime)
    status = wsme.wsattr(wtypes.text, readonly=True)
    properties = {wtypes.text: types.jsontype}
    availabilities = wsme.wsattr([[datetime.datetime]], readonly=True)

    def __init__(self, **kwargs):

        self.fields = offer.Offer.fields
        for field in self.fields:
            setattr(self, field, kwargs.get(field, wtypes.Unset))

        setattr(self, 'availabilities', kwargs.get('availabilities',
                                                   wtypes.Unset))


class OfferCollection(types.Collection):
    offers = [Offer]

    def __init__(self, **kwargs):
        self._type = 'offers'


class OffersController(rest.RestController):

    @wsme_pecan.wsexpose(Offer, wtypes.text)
    def get_one(self, offer_id):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:offer:get', cdict, cdict)

        o_object = utils.get_offer(offer_id)
        o = OffersController._add_offer_availabilities(o_object)
        return Offer(**o)

    @wsme_pecan.wsexpose(OfferCollection, wtypes.text, wtypes.text,
                         wtypes.text, datetime.datetime, datetime.datetime,
                         datetime.datetime, datetime.datetime,
                         wtypes.text)
    def get_all(self, project_id=None, resource_type=None,
                resource_uuid=None, start_time=None, end_time=None,
                available_start_time=None, available_end_time=None,
                status=None):

        request = pecan.request.context

        cdict = request.to_policy_values()
        policy.authorize('esi_leap:offer:get', cdict, cdict)

        if (start_time and end_time is None) or\
           (end_time and start_time is None):
            raise exception.InvalidTimeAPICommand(resource='an offer',
                                                  start_time=str(start_time),
                                                  end_time=str(end_time))

        if start_time and end_time and\
           end_time <= start_time:
            raise exception.InvalidTimeAPICommand(resource='an offer',
                                                  start_time=str(start_time),
                                                  end_time=str(end_time))

        if (available_start_time and available_end_time is None) or\
           (available_end_time and available_start_time is None):
            raise exception.InvalidAvailabilityAPICommand(
                a_start=str(start_time),
                a_end=str(end_time))

        if available_start_time and available_end_time and\
                available_end_time <= available_start_time:
            raise exception.InvalidAvailabilityAPICommand(
                a_start=available_start_time,
                a_end=available_end_time)

        if status is None:
            status = statuses.AVAILABLE
        elif status == 'any':
            status = None

        possible_filters = {
            'project_id': project_id,
            'resource_type': resource_type,
            'resource_uuid': resource_uuid,
            'status': status,
            'start_time': start_time,
            'end_time': end_time,
            'available_start_time': available_start_time,
            'available_end_time': available_end_time,
        }

        filters = {}
        for k, v in possible_filters.items():
            if v is not None:
                filters[k] = v

        offer_collection = OfferCollection()
        offers = offer.Offer.get_all(filters, request)

        offer_collection.offers = [
            Offer(**OffersController._add_offer_availabilities(o))
            for o in offers]
        return offer_collection

    @wsme_pecan.wsexpose(Offer, body=Offer)
    def post(self, new_offer):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:offer:create', cdict, cdict)

        offer_dict = new_offer.to_dict()
        offer_dict['project_id'] = request.project_id

        utils.verify_resource_permission(cdict, offer_dict)

        offer_dict['uuid'] = uuidutils.generate_uuid()

        if 'start_time' not in offer_dict:
            offer_dict['start_time'] = datetime.datetime.now()
        if 'end_time' not in offer_dict:
            offer_dict['end_time'] = datetime.datetime.max

        if offer_dict['start_time'] >= offer_dict['end_time']:
            raise exception.\
                InvalidTimeRange(resource="an offer",
                                 start_time=str(offer_dict['start_time']),
                                 end_time=str(offer_dict['end_time']))

        o = offer.Offer(**offer_dict)
        o.create()
        o = OffersController._add_offer_availabilities(o)
        return Offer(**o)

    @wsme_pecan.wsexpose(Offer, wtypes.text)
    def delete(self, offer_id):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:offer:delete', cdict, cdict)

        o_object = utils.get_offer_authorized(offer_id,
                                              cdict,
                                              statuses.AVAILABLE)

        o_object.cancel()

    @staticmethod
    def _add_offer_availabilities(o):
        availabilities = o.get_availabilities()
        o = o.to_dict()
        o['availabilities'] = availabilities
        return o
