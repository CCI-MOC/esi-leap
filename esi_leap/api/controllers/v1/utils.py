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

from oslo_policy import policy as oslo_policy
from oslo_utils import uuidutils

from esi_leap.common import exception
from esi_leap.common import policy
from esi_leap.objects import contract
from esi_leap.objects import offer
from esi_leap.resource_objects import resource_object_factory as ro_factory


def get_offer_authorized(uuid_or_name, cdict, status_filter=None):
    if uuidutils.is_uuid_like(uuid_or_name):
        o = offer.Offer.get(uuid_or_name)
        offer_objs = []

        if not status_filter or o.status == status_filter:
            try:
                if o.project_id != cdict['project_id']:
                    policy.authorize('esi_leap:offer:offer_admin',
                                     cdict, cdict)
                offer_objs.append(o)
            except oslo_policy.PolicyNotAuthorized:
                pass

    else:
        try:
            policy.authorize('esi_leap:offer:offer_admin', cdict, cdict)
            offer_objs = offer.Offer.get_all({'name': uuid_or_name,
                                              'status': status_filter})

        except oslo_policy.PolicyNotAuthorized:
            offer_objs = offer.Offer.get_all(
                {'name': uuid_or_name,
                 'project_id': cdict['project_id'],
                 'status': status_filter}
            )

    if len(offer_objs) == 0:
        raise exception.OfferNotFound(offer_uuid=uuid_or_name)
    elif len(offer_objs) > 1:
        raise exception.OfferDuplicateName(name=uuid_or_name)

    return offer_objs[0]


def verify_resource_permission(cdict, offer_dict):
    resource_type = offer_dict.get('resource_type')
    resource_uuid = offer_dict.get('resource_uuid')
    resource = ro_factory.ResourceObjectFactory.get_resource_object(
        resource_type, resource_uuid)
    if not resource.is_resource_admin(offer_dict['project_id']):
        policy.authorize('esi_leap:offer:offer_admin', cdict, cdict)


def get_offer(uuid_or_name, status_filter=None):
    if uuidutils.is_uuid_like(uuid_or_name):
        o = offer.Offer.get(uuid_or_name)
        if not status_filter or o.status == status_filter:
            return o
        else:
            raise exception.OfferNotFound(
                offer_uuid=uuid_or_name)
    else:
        offer_objs = offer.Offer.get_all({'name': uuid_or_name,
                                          'status': status_filter})

        if len(offer_objs) > 1:
            raise exception.OfferDuplicateName(
                name=uuid_or_name)
        elif len(offer_objs) == 0:
            raise exception.OfferNotFound(
                offer_uuid=uuid_or_name)

        return offer_objs[0]


def get_contract_authorized(uuid_or_name, cdict, status_filters=[]):

    if uuidutils.is_uuid_like(uuid_or_name):
        c = contract.Contract.get(uuid_or_name)
        contract_objs = []
        if not status_filters or c.status in status_filters:
            contract_objs.append(c)

    else:
        contract_objs = contract.Contract.get_all({'name': uuid_or_name,
                                                   'status': status_filters})

    permitted = []
    for c in contract_objs:
        try:
            contract_authorize_management(c, cdict)
            permitted.append(c)
        except oslo_policy.PolicyNotAuthorized:
            continue

        if len(permitted) > 1:
            raise exception.ContractDuplicateName(name=uuid_or_name)

    if len(permitted) == 0:
        raise exception.ContractNotFound(contract_id=uuid_or_name)

    return permitted[0]


def contract_authorize_management(c, cdict):

    if c.project_id != cdict['project_id']:
        try:
            policy.authorize('esi_leap:contract:contract_admin',
                             cdict, cdict)
        except oslo_policy.PolicyNotAuthorized:
            o = offer.Offer.get(c.offer_uuid)
            if o.project_id != cdict['project_id']:
                policy.authorize('esi_leap:offer:offer_admin',
                                 cdict, cdict)
