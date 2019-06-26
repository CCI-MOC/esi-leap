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
from esi_leap.common import policy
from esi_leap.objects import contract


class Contract(base.ESILEAPBase):

    id = wsme.wsattr(int)
    uuid = wsme.wsattr(wtypes.text)
    project_id = wsme.wsattr(wtypes.text)
    start_date = wsme.wsattr(datetime.datetime)
    end_date = wsme.wsattr(datetime.datetime)
    status = wsme.wsattr(wtypes.text)
    properties = {wtypes.text: types.jsontype}
    offer_uuid = wsme.wsattr(wtypes.text)

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
        return Contract(**c.to_dict())

    @wsme_pecan.wsexpose(ContractCollection)
    def get_all(self):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:contract:get', cdict, cdict)

        contract_collection = ContractCollection()
        contracts = contract.Contract.get_all(request)
        contract_collection.contracts = [
            Contract(**c.to_dict()) for c in contracts]
        return contract_collection

    @wsme_pecan.wsexpose(Contract, body=Contract)
    def post(self, new_contract):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:contract:create', cdict, cdict)

        c = contract.Contract(**new_contract.to_dict())
        c.create(request)
        return Contract(**c.to_dict())

    @wsme_pecan.wsexpose(Contract, wtypes.text)
    def delete(self, contract_uuid):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:contract:delete', cdict, cdict)

        c = contract.Contract.get(request, contract_uuid)
        c.destroy(pecan.request.context)
