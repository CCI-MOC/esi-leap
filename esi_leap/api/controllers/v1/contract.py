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
from esi_leap.common import exception
from esi_leap.common import policy
from esi_leap.common import statuses
from esi_leap.objects import contract
from esi_leap.objects import offer


class Contract(base.ESILEAPBase):

    uuid = wsme.wsattr(wtypes.text, readonly=True)
    project_id = wsme.wsattr(wtypes.text)
    start_time = wsme.wsattr(datetime.datetime)
    end_time = wsme.wsattr(datetime.datetime)
    status = wsme.wsattr(wtypes.text, readonly=True)
    properties = {wtypes.text: types.jsontype}
    offer_uuid = wsme.wsattr(wtypes.text, mandatory=True)

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
    def get_one(self, contract_uuid):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:contract:get', cdict, cdict)

        c = contract.Contract.get(request, contract_uuid)

        if c.project_id != request.project_id:
            o = offer.Offer.get(request.project_id, c.offer_uuid)
            if o.project_id != request.project_id:
                policy.authorize('esi_leap:contract:get_admin', cdict, cdict)

        return Contract(**c.to_dict())

    @wsme_pecan.wsexpose(ContractCollection, wtypes.text,
                         datetime.datetime, datetime.datetime, wtypes.text,
                         wtypes.text, wtypes.text, wtypes.text)
    def get_all(self, project_id=None, start_time=None, end_time=None,
                status=None, offer_uuid=None, view=None, owner=None):
        request = pecan.request.context
        cdict = request.to_policy_values()

        filters = ContractsController.\
            _contract_get_all_authorize_filters(
                cdict, request.project_id,
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

        if 'project_id' in contract_dict:
            if contract_dict['project_id'] != request.project_id:
                policy.authorize('esi_leap:contract:contract_admin',
                                 cdict, cdict)
        else:
            contract_dict['project_id'] = request.project_id

        c = contract.Contract(**contract_dict)
        c.create(request)

        return Contract(**c.to_dict())

    @wsme_pecan.wsexpose(Contract, wtypes.text)
    def delete(self, contract_uuid):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:contract:delete', cdict, cdict)

        c = contract.Contract.get(request, contract_uuid)
        if c.project_id != request.project_id:
            o = offer.Offer.get(request.project_id, c.offer_uuid)
            if o.project_id != request.project_id:
                policy.authorize('esi_leap:contract:contract_admin',
                                 cdict, cdict)

        c.cancel()

    @staticmethod
    def _contract_get_all_authorize_filters(cdict, r_project_id,
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
                if owner == 'self':
                    possible_filters['owner'] = cdict['project_id']
                else:
                    if r_project_id != owner:
                        policy.authorize('esi_leap:contract:contract_admin',
                                         cdict, cdict)
                    possible_filters['owner'] = owner
                possible_filters['project_id'] = project_id
            else:

                if project_id is None:
                    project_id = r_project_id
                else:
                    if project_id != r_project_id:
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
