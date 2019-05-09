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

import pecan
from pecan import rest
import wsme
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from esi_leap.api.controllers import types
from esi_leap.objects import policy


class Policy(wtypes.Base):
    id = wsme.wsattr(int)
    uuid = wsme.wsattr(wtypes.text)
    name = wsme.wsattr(wtypes.text)
    max_time_for_lease = wsme.wsattr(int)
    extendible = wsme.wsattr(bool)


class PolicyCollection(types.Collection):
    policies = [Policy]

    def __init__(self, **kwargs):
        self._type = 'policies'


class PoliciesController(rest.RestController):

    @wsme_pecan.wsexpose(Policy, wtypes.text)
    def get_one(self, policy_uuid):
        p = policy.Policy.get(pecan.request.context, policy_uuid)
        return Policy(**p.to_dict())

    @wsme_pecan.wsexpose(PolicyCollection)
    def get_all(self):
        policy_collection = PolicyCollection()
        policies = policy.Policy.get_all(pecan.request.context)
        policy_collection.policies = [Policy(**p.to_dict()) for p in policies]
        return policy_collection
