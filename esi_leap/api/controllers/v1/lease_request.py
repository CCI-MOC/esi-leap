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
from esi_leap.objects import lease_request


class LeaseRequest(base.ESILEAPBase):

    id = wsme.wsattr(int)
    uuid = wsme.wsattr(wtypes.text)
    name = wsme.wsattr(wtypes.text)
    node_properties = {wtypes.text: types.jsontype}
    min_nodes = wsme.wsattr(int)
    max_nodes = wsme.wsattr(int)
    lease_time = wsme.wsattr(int)
    status = wsme.wsattr(wtypes.text)
    cancel_date = wsme.wsattr(datetime.datetime)
    fulfilled_date = wsme.wsattr(datetime.datetime)
    expiration_date = wsme.wsattr(datetime.datetime)

    def __init__(self, **kwargs):
        self.fields = lease_request.LeaseRequest.fields
        for field in self.fields:
            setattr(self, field, kwargs.get(field, wtypes.Unset))


class LeaseRequestCollection(types.Collection):
    lease_requests = [LeaseRequest]

    def __init__(self, **kwargs):
        self._type = 'lease_requests'


class LeaseRequestsController(rest.RestController):

    @wsme_pecan.wsexpose(LeaseRequest, wtypes.text)
    def get_one(self, lease_request_uuid):
        r = lease_request.LeaseRequest.get(
            pecan.request.context, lease_request_uuid)
        return LeaseRequest(**r.to_dict())

    @wsme_pecan.wsexpose(LeaseRequestCollection)
    def get_all(self):
        lease_request_collection = LeaseRequestCollection()
        lease_requests = lease_request.LeaseRequest.get_all(
            pecan.request.context)
        lease_request_collection.lease_requests = [
            LeaseRequest(**r.to_dict()) for r in lease_requests]
        return lease_request_collection

    @wsme_pecan.wsexpose(LeaseRequest, body=LeaseRequest)
    def post(self, new_lease_request):
        r = lease_request.LeaseRequest(**new_lease_request.to_dict())
        r.create(pecan.request.context)
        return LeaseRequest(**r.to_dict())

    @wsme_pecan.wsexpose(LeaseRequest, wtypes.text)
    def delete(self, lease_request_uuid):
        r = lease_request.LeaseRequest.get(
            pecan.request.context, lease_request_uuid)
        r.destroy(pecan.request.context)
