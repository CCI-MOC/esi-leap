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

import concurrent.futures
import datetime
import http.client as http_client
from oslo_utils import uuidutils
import pecan
from pecan import rest
import wsme
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from esi_leap.api.controllers import base
from esi_leap.api.controllers import types
from esi_leap.api.controllers.v1 import lease
from esi_leap.api.controllers.v1 import utils
from esi_leap.common import exception
from esi_leap.common import ironic
from esi_leap.common import keystone
from esi_leap.common import statuses
import esi_leap.conf
from esi_leap.objects import lease as lease_obj
from esi_leap.objects import offer as offer_obj
from esi_leap.resource_objects import get_resource_object

CONF = esi_leap.conf.CONF


class Offer(base.ESILEAPBase):

    name = wsme.wsattr(wtypes.text)
    uuid = wsme.wsattr(wtypes.text, readonly=True)
    project_id = wsme.wsattr(wtypes.text, readonly=True)
    project = wsme.wsattr(wtypes.text, readonly=True)
    lessee_id = wsme.wsattr(wtypes.text)
    lessee = wsme.wsattr(wtypes.text, readonly=True)
    resource_type = wsme.wsattr(wtypes.text)
    resource_uuid = wsme.wsattr(wtypes.text, mandatory=True)
    resource = wsme.wsattr(wtypes.text, readonly=True)
    resource_class = wsme.wsattr(wtypes.text)
    start_time = wsme.wsattr(datetime.datetime)
    end_time = wsme.wsattr(datetime.datetime)
    status = wsme.wsattr(wtypes.text, readonly=True)
    properties = {wtypes.text: types.jsontype}
    availabilities = wsme.wsattr([[datetime.datetime]], readonly=True)
    parent_lease_uuid = wsme.wsattr(wtypes.text, readonly=True)

    def __init__(self, **kwargs):

        self.fields = offer_obj.Offer.fields
        for field in self.fields:
            setattr(self, field, kwargs.get(field, wtypes.Unset))

        for attr in ('availabilities', 'project', 'lessee',
                     'resource', 'resource_class'):
            setattr(self, attr, kwargs.get(attr, wtypes.Unset))


class OfferCollection(types.Collection):
    offers = [Offer]

    def __init__(self, **kwargs):
        self._type = 'offers'


class OffersController(rest.RestController):

    _custom_actions = {
        'claim': ['POST']
    }

    @wsme_pecan.wsexpose(Offer, wtypes.text)
    def get_one(self, offer_id):
        request = pecan.request.context
        cdict = request.to_policy_values()

        offer = utils.check_offer_policy_and_retrieve(
            request, 'esi_leap:offer:get', offer_id)
        utils.check_offer_lessee(cdict, offer)

        o = utils.offer_get_dict_with_added_info(offer)

        return Offer(**o)

    @wsme_pecan.wsexpose(OfferCollection, wtypes.text, wtypes.text,
                         wtypes.text, wtypes.text, datetime.datetime,
                         datetime.datetime, datetime.datetime,
                         datetime.datetime, wtypes.text)
    def get_all(self, project_id=None, resource_type=None,
                resource_class=None, resource_uuid=None,
                start_time=None, end_time=None,
                available_start_time=None, available_end_time=None,
                status=None):
        request = pecan.request.context
        cdict = request.to_policy_values()
        utils.policy_authorize('esi_leap:offer:get_all', cdict, cdict)

        if project_id is not None:
            project_id = keystone.get_project_uuid_from_ident(project_id)

        if resource_uuid is not None:
            if resource_type is None:
                resource_type = CONF.api.default_resource_type
            resource = get_resource_object(resource_type, resource_uuid)
            resource_uuid = resource.get_uuid()

        # either both are defined or both are None
        if bool(start_time) != bool(end_time):
            raise exception.InvalidTimeAPICommand(resource='an offer',
                                                  start_time=str(start_time),
                                                  end_time=str(end_time))
        if (start_time or end_time) and (end_time <= start_time):
            raise exception.InvalidTimeAPICommand(resource='an offer',
                                                  start_time=str(start_time),
                                                  end_time=str(end_time))

        if bool(available_start_time) != bool(available_end_time):
            raise exception.InvalidAvailabilityAPICommand(
                a_start=str(available_start_time),
                a_end=str(available_end_time))
        if ((available_start_time or available_end_time) and
                (available_end_time <= available_start_time)):
            raise exception.InvalidAvailabilityAPICommand(
                a_start=str(available_start_time),
                a_end=str(available_end_time))

        if status is None:
            status = statuses.OFFER_CAN_DELETE
        elif status == 'any':
            status = None
        else:
            status = [status]

        try:
            utils.policy_authorize('esi_leap:offer:offer_admin', cdict, cdict)
            lessee_id = None
        except exception.HTTPForbidden:
            lessee_id = cdict['project_id']

        filters = {
            'project_id': project_id,
            'lessee_id': lessee_id,
            'resource_type': resource_type,
            'resource_uuid': resource_uuid,
            'status': status,
            'start_time': start_time,
            'end_time': end_time,
            'available_start_time': available_start_time,
            'available_end_time': available_end_time,
        }

        # unpack iterator to tuple so we can use 'del'
        for k, v in tuple(filters.items()):
            if v is None:
                del filters[k]

        offer_collection = OfferCollection()
        offers = offer_obj.Offer.get_all(filters, request)

        offer_collection.offers = []

        if len(offers) > 0:
            project_list = None
            node_list = None
            with concurrent.futures.ThreadPoolExecutor() as executor:
                f1 = executor.submit(ironic.get_node_list)
                f2 = executor.submit(keystone.get_project_list)
                node_list = f1.result()
                project_list = f2.result()

            offers_with_added_info = [
                Offer(**utils.offer_get_dict_with_added_info(o, project_list,
                                                             node_list))
                for o in offers]
            if resource_class:
                offer_collection.offers = [
                    o for o in offers_with_added_info
                    if o.resource_class == resource_class]
            else:
                offer_collection.offers = offers_with_added_info

        return offer_collection

    @wsme_pecan.wsexpose(Offer, body=Offer, status_code=http_client.CREATED)
    def post(self, new_offer):
        request = pecan.request.context
        cdict = request.to_policy_values()
        utils.policy_authorize('esi_leap:offer:create', cdict, cdict)

        offer_dict = new_offer.to_dict()
        offer_dict['project_id'] = request.project_id
        offer_dict['uuid'] = uuidutils.generate_uuid()
        if 'resource_type' not in offer_dict:
            offer_dict['resource_type'] = CONF.api.default_resource_type
        resource = get_resource_object(offer_dict['resource_type'],
                                       offer_dict['resource_uuid'])
        offer_dict['resource_uuid'] = resource.get_uuid()

        if 'lessee_id' in offer_dict:
            offer_dict['lessee_id'] = keystone.get_project_uuid_from_ident(
                offer_dict['lessee_id'])

        if 'start_time' not in offer_dict:
            offer_dict['start_time'] = datetime.datetime.now()
        if 'end_time' not in offer_dict:
            offer_dict['end_time'] = datetime.datetime.max

        if offer_dict['start_time'] >= offer_dict['end_time']:
            raise exception.InvalidTimeRange(
                resource='an offer',
                start_time=str(offer_dict['start_time']),
                end_time=str(offer_dict['end_time']))

        try:
            utils.check_resource_admin(cdict, resource, request.project_id)
        except exception.HTTPResourceForbidden:
            parent_lease_uuid = utils.check_resource_lease_admin(
                cdict,
                resource,
                request.project_id,
                offer_dict.get('start_time'),
                offer_dict.get('end_time'))
            if parent_lease_uuid is None:
                raise
            offer_dict['parent_lease_uuid'] = parent_lease_uuid

        o = offer_obj.Offer(**offer_dict)
        o.create()
        return Offer(**utils.offer_get_dict_with_added_info(o))

    @wsme_pecan.wsexpose(Offer, wtypes.text)
    def delete(self, offer_id):
        request = pecan.request.context

        offer = utils.check_offer_policy_and_retrieve(
            request, 'esi_leap:offer:delete', offer_id,
            statuses.OFFER_CAN_DELETE)
        offer.cancel()

    @wsme_pecan.wsexpose(lease.Lease, wtypes.text, body=lease.Lease,
                         status_code=http_client.CREATED)
    def claim(self, offer_uuid, new_lease):
        request = pecan.request.context
        cdict = request.to_policy_values()

        offer = utils.check_offer_policy_and_retrieve(
            request, 'esi_leap:offer:claim', offer_uuid, [statuses.AVAILABLE])
        utils.check_offer_lessee(cdict, offer)

        lease_dict = new_lease.to_dict()
        lease_dict['project_id'] = request.project_id
        lease_dict['uuid'] = uuidutils.generate_uuid()
        lease_dict['offer_uuid'] = offer_uuid
        lease_dict['resource_type'] = offer.resource_type
        lease_dict['resource_uuid'] = offer.resource_uuid
        lease_dict['owner_id'] = offer.project_id

        if offer.parent_lease_uuid is not None:
            lease_dict['parent_lease_uuid'] = offer.parent_lease_uuid

        if 'start_time' not in lease_dict:
            lease_dict['start_time'] = datetime.datetime.now()

        if 'end_time' not in lease_dict:
            q = offer.get_first_availability(lease_dict['start_time'])
            if q is None:
                lease_dict['end_time'] = offer.end_time
            else:
                lease_dict['end_time'] = q.start_time

        new_lease = lease_obj.Lease(**lease_dict)
        new_lease.create(request)
        return lease.Lease(**utils.lease_get_dict_with_added_info(new_lease))
