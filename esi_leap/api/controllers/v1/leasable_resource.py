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
from esi_leap.objects import leasable_resource


class LeasableResource(base.ESILEAPBase):

    id = wsme.wsattr(int)
    resource_type = wsme.wsattr(wtypes.text)
    resource_uuid = wsme.wsattr(wtypes.text)
    policy_uuid = wsme.wsattr(wtypes.text)
    expiration_date = wsme.wsattr(datetime.datetime)
    request_uuid = wsme.wsattr(wtypes.text)
    lease_expiration_date = wsme.wsattr(datetime.datetime)

    def __init__(self, **kwargs):
        self.fields = leasable_resource.LeasableResource.fields
        for field in self.fields:
            setattr(self, field, kwargs.get(field, wtypes.Unset))


class LeasableResourceCollection(types.Collection):
    leasable_resources = [LeasableResource]

    def __init__(self, **kwargs):
        self._type = 'leasable_resources'


class LeasableResourcesController(rest.RestController):

    @wsme_pecan.wsexpose(LeasableResource, wtypes.text, wtypes.text)
    def get_one(self, resource_type, resource_uuid):
        r = leasable_resource.LeasableResource.get(
            pecan.request.context, resource_type, resource_uuid)
        return LeasableResource(**r.to_dict())

    @wsme_pecan.wsexpose(LeasableResourceCollection)
    def get_all(self):
        leasable_resource_collection = LeasableResourceCollection()
        leasable_resources = leasable_resource.LeasableResource.get_all(
            pecan.request.context)
        leasable_resource_collection.leasable_resources = [
            LeasableResource(**r.to_dict()) for r in leasable_resources]
        return leasable_resource_collection

    @wsme_pecan.wsexpose(LeasableResource, body=LeasableResource)
    def post(self, new_leasable_resource):
        r = leasable_resource.LeasableResource(
            **new_leasable_resource.to_dict())
        r.create(pecan.request.context)
        return LeasableResource(**r.to_dict())

    @wsme_pecan.wsexpose(LeasableResource, wtypes.text, wtypes.text)
    def delete(self, resource_type, resource_uuid):
        r = leasable_resource.LeasableResource.get(
            pecan.request.context, resource_type, resource_uuid)
        r.destroy(pecan.request.context)
