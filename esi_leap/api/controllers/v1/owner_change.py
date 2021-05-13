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
import http.client as http_client
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
import esi_leap.conf
from esi_leap.objects import owner_change as owner_change_obj

CONF = esi_leap.conf.CONF


class OwnerChange(base.ESILEAPBase):

    uuid = wsme.wsattr(wtypes.text, readonly=True)
    from_owner_id = wsme.wsattr(wtypes.text, mandatory=True)
    to_owner_id = wsme.wsattr(wtypes.text, mandatory=True)
    resource_type = wsme.wsattr(wtypes.text)
    resource_uuid = wsme.wsattr(wtypes.text, mandatory=True)
    start_time = wsme.wsattr(datetime.datetime)
    end_time = wsme.wsattr(datetime.datetime)
    status = wsme.wsattr(wtypes.text, readonly=True)
    fulfill_time = wsme.wsattr(datetime.datetime, readonly=True)
    expire_time = wsme.wsattr(datetime.datetime, readonly=True)

    def __init__(self, **kwargs):
        self.fields = owner_change_obj.OwnerChange.fields
        for field in self.fields:
            setattr(self, field, kwargs.get(field, wtypes.Unset))


class OwnerChangeCollection(types.Collection):
    owner_changes = [OwnerChange]

    def __init__(self, **kwargs):
        self._type = 'owner_changes'


class OwnerChangesController(rest.RestController):

    @wsme_pecan.wsexpose(OwnerChange, wtypes.text)
    def get_one(self, owner_change_uuid):
        request = pecan.request.context
        cdict = request.to_policy_values()

        policy.authorize('esi_leap:owner_change:get', cdict, cdict)

        oc = owner_change_obj.OwnerChange.get(owner_change_uuid)
        if oc is None:
            raise exception.OwnerChangeNotFound(
                owner_change_uuid=owner_change_uuid)

        if cdict['project_id'] not in (oc.from_owner_id, oc.to_owner_id):
            policy.authorize('esi_leap:owner_change:owner_change_admin',
                             cdict, cdict)

        return OwnerChange(**oc.to_dict())

    @wsme_pecan.wsexpose(OwnerChangeCollection, wtypes.text, wtypes.text,
                         wtypes.text, wtypes.text,
                         datetime.datetime, datetime.datetime,
                         wtypes.text)
    def get_all(self, from_owner_id=None, to_owner_id=None,
                resource_type=None, resource_uuid=None,
                start_time=None, end_time=None,
                status=None):
        request = pecan.request.context

        cdict = request.to_policy_values()
        policy.authorize('esi_leap:owner_change:get', cdict, cdict)

        if (start_time and end_time is None) or\
           (end_time and start_time is None):
            raise exception.InvalidTimeAPICommand(resource='an owner change',
                                                  start_time=str(start_time),
                                                  end_time=str(end_time))

        if start_time and end_time and\
           end_time <= start_time:
            raise exception.InvalidTimeAPICommand(resource='an owner change',
                                                  start_time=str(start_time),
                                                  end_time=str(end_time))

        if status is None:
            status = [statuses.CREATED, statuses.ACTIVE]
        elif status == 'any':
            status = None

        try:
            policy.authorize('esi_leap:owner_change:owner_change_admin',
                             cdict, cdict)
            from_or_to_owner_id = None
        except oslo_policy.PolicyNotAuthorized:
            from_or_to_owner_id = cdict['project_id']

        possible_filters = {
            'from_or_to_owner_id': from_or_to_owner_id,
            'from_owner_id': from_owner_id,
            'to_owner_id': to_owner_id,
            'resource_type': resource_type,
            'resource_uuid': resource_uuid,
            'status': status,
            'start_time': start_time,
            'end_time': end_time,
        }

        filters = {}
        for k, v in possible_filters.items():
            if v is not None:
                filters[k] = v

        oc_collection = OwnerChangeCollection()
        ocs = owner_change_obj.OwnerChange.get_all(filters, request)
        oc_collection.owner_changes = [
            OwnerChange(**oc.to_dict()) for oc in ocs]

        return oc_collection

    @wsme_pecan.wsexpose(OwnerChange, body=OwnerChange,
                         status_code=http_client.CREATED)
    def post(self, new_owner_change):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:owner_change:create', cdict, cdict)

        owner_change_dict = new_owner_change.to_dict()
        owner_change_dict['uuid'] = uuidutils.generate_uuid()

        if owner_change_dict['from_owner_id'] == \
           owner_change_dict['to_owner_id']:
            raise exception.OwnerChangeSameFromAndToOwner()

        if 'resource_type' not in owner_change_dict:
            owner_change_dict['resource_type'] = CONF.api.default_resource_type

        if 'start_time' not in owner_change_dict:
            owner_change_dict['start_time'] = datetime.datetime.now()
        if 'end_time' not in owner_change_dict:
            owner_change_dict['end_time'] = datetime.datetime.max

        if owner_change_dict['start_time'] >= owner_change_dict['end_time']:
            raise exception.\
                InvalidTimeRange(
                    resource="an owner change",
                    start_time=str(owner_change_dict['start_time']),
                    end_time=str(owner_change_dict['end_time']))

        oc = owner_change_obj.OwnerChange(**owner_change_dict)
        oc.create()
        return OwnerChange(**oc.to_dict())

    @wsme_pecan.wsexpose(OwnerChange, wtypes.text)
    def delete(self, owner_change_uuid):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:owner_change:delete', cdict, cdict)

        oc = owner_change_obj.OwnerChange.get(owner_change_uuid)
        if oc is None:
            raise exception.OwnerChangeNotFound(
                owner_change_uuid=owner_change_uuid)

        if cdict['project_id'] not in (oc.from_owner_id, oc.to_owner_id):
            policy.authorize('esi_leap:owner_change:owner_change_admin',
                             cdict, cdict)

        oc.cancel()
