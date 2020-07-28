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
from oslo_policy import policy as oslo_policy
from oslo_utils import uuidutils
import pecan
from pecan import rest
import wsme
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from esi_leap.api.controllers import base
from esi_leap.api.controllers import types
from esi_leap.common import exception
from esi_leap.common import policy
from esi_leap.common import statuses
from esi_leap.objects import contract
from esi_leap.objects import offer


class Contract(base.ESILEAPBase):

    name = wsme.wsattr(wtypes.text)
    uuid = wsme.wsattr(wtypes.text, readonly=True)
    project_id = wsme.wsattr(wtypes.text, readonly=True)
    start_time = wsme.wsattr(datetime.datetime)
    end_time = wsme.wsattr(datetime.datetime)
    status = wsme.wsattr(wtypes.text, readonly=True)
    properties = {wtypes.text: types.jsontype}
    offer_uuid = wsme.wsattr(wtypes.text, readonly=True)
    offer_uuid_or_name = wsme.wsattr(wtypes.text)

    def __init__(self, **kwargs):
        self.fields = contract.Contract.fields
        for field in self.fields:
            setattr(self, field, kwargs.get(field, wtypes.Unset))


class ContractCollection(types.Collection):
    contracts = [Contract]

    def __init__(self, **kwargs):
        self._type = 'contracts'


class ContractsController(rest.RestController):

    @wsme_pecan.wsexpose(Contract, wtypes.text)
    def get_one(self, contract_id):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:contract:get', cdict, cdict)

        permitted = ContractsController._contract_get_authorized_contract(
            contract_id, cdict)

        return Contract(**permitted.to_dict())

    @wsme_pecan.wsexpose(ContractCollection, wtypes.text,
                         datetime.datetime, datetime.datetime, wtypes.text,
                         wtypes.text, wtypes.text, wtypes.text)
    def get_all(self, project_id=None, start_time=None, end_time=None,
                status=None, offer_uuid=None, view=None, owner=None):
        request = pecan.request.context
        cdict = request.to_policy_values()

        filters = ContractsController.\
            _contract_get_all_authorize_filters(
                cdict,
                project_id=project_id, start_time=start_time,
                end_time=end_time, status=status,
                offer_uuid=offer_uuid, view=view, owner=owner)

        contract_collection = ContractCollection()
        contracts = contract.Contract.get_all(request, filters)
        contract_collection.contracts = [
            Contract(**c.to_dict()) for c in contracts]
        return contract_collection

    @wsme_pecan.wsexpose(Contract, body=Contract)
    def post(self, new_contract):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:contract:create', cdict, cdict)

        contract_dict = new_contract.to_dict()
        contract_dict['project_id'] = request.project_id
        contract_dict['uuid'] = uuidutils.generate_uuid()

        if new_contract.offer_uuid_or_name is None:
            raise exception.ContractNoOfferUUID()

        o_objects = offer.Offer.get(new_contract.offer_uuid_or_name)
        if len(o_objects) > 1:
            raise exception.OfferDuplicateName(
                name=new_contract.offer_uuid_or_name)
        elif len(o_objects) == 0:
            raise exception.OfferNotFound(
                offer_uuid=new_contract.offer_uuid_or_name)

        related_offer = o_objects[0]
        contract_dict['offer_uuid'] = related_offer.uuid

        if 'start_time' not in contract_dict:
            contract_dict['start_time'] = datetime.datetime.now()

        if 'end_time' not in contract_dict:
            q = related_offer.get_first_availability(
                contract_dict['start_time'])
            if q is None:
                contract_dict['end_time'] = related_offer.end_time
            else:
                contract_dict['end_time'] = q.start_time

        c = contract.Contract(**contract_dict)
        c.create(request)
        return Contract(**c.to_dict())

    @wsme_pecan.wsexpose(Contract, wtypes.text)
    def delete(self, contract_id):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:contract:delete', cdict, cdict)

        permitted = ContractsController._contract_get_authorized_contract(
            contract_id, cdict)

        permitted.cancel()

    @staticmethod
    def _contract_get_authorized_contract(contract_id, cdict):

        contract_objs = contract.Contract.get(contract_id)
        permitted = []
        for c in contract_objs:
            try:
                ContractsController._contract_authorize_management(c, cdict)
                permitted.append(c)
            except oslo_policy.PolicyNotAuthorized:
                continue

            if len(permitted) > 1:
                raise exception.ContractDuplicateName(name=contract_id)

        if len(permitted) == 0:
            raise exception.ContractNotFound(contract_id=contract_id)

        return permitted[0]

    @staticmethod
    def _contract_authorize_management(c, cdict):

        if c.project_id != cdict['project_id']:
            try:
                policy.authorize('esi_leap:contract:contract_admin',
                                 cdict, cdict)
            except oslo_policy.PolicyNotAuthorized:
                o = offer.Offer.get_by_uuid(c.offer_uuid)
                if o.project_id != cdict['project_id']:
                    policy.authorize('esi_leap:offer:offer_admin',
                                     cdict, cdict)

    @staticmethod
    def _contract_get_all_authorize_filters(cdict,
                                            start_time=None, end_time=None,
                                            status=None, offer_uuid=None,
                                            project_id=None, view=None,
                                            owner=None):

        if status is None:
            status = [statuses.CREATED, statuses.ACTIVE]
        elif status == 'any':
            status = None

        possible_filters = {
            'status': status,
            'offer_uuid': offer_uuid,
            'start_time': start_time,
            'end_time': end_time,
        }

        if view == 'all':
            policy.authorize('esi_leap:contract:contract_admin', cdict, cdict)
            possible_filters['owner'] = owner
            possible_filters['project_id'] = project_id
        else:
            policy.authorize('esi_leap:contract:get', cdict, cdict)

            if owner:
                if cdict['project_id'] != owner:
                    policy.authorize('esi_leap:contract:contract_admin',
                                     cdict, cdict)

                possible_filters['owner'] = owner
                possible_filters['project_id'] = project_id
            else:

                if project_id is None:
                    project_id = cdict['project_id']
                elif project_id != cdict['project_id']:
                    policy.authorize('esi_leap:contract:contract_admin',
                                     cdict, cdict)

                possible_filters['project_id'] = project_id

        if (start_time and end_time is None) or \
                (end_time and start_time is None):
            raise exception.InvalidTimeAPICommand(resource="a contract",
                                                  start_time=str(start_time),
                                                  end_time=str(end_time))

        if start_time and end_time and\
           end_time <= start_time:
            raise exception.InvalidTimeAPICommand(resource='a contract',
                                                  start_time=str(start_time),
                                                  end_time=str(end_time))

        filters = {}
        for k, v in possible_filters.items():
            if v is not None:
                filters[k] = v

        return filters
