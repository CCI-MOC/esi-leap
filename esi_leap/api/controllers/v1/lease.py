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
from esi_leap.common import keystone
from esi_leap.common import policy
from esi_leap.common import statuses
import esi_leap.conf
from esi_leap.objects import lease as lease_obj
from esi_leap.resource_objects import resource_object_factory as ro_factory

CONF = esi_leap.conf.CONF


class Lease(base.ESILEAPBase):

    name = wsme.wsattr(wtypes.text)
    uuid = wsme.wsattr(wtypes.text, readonly=True)
    project_id = wsme.wsattr(wtypes.text)
    owner_id = wsme.wsattr(wtypes.text, readonly=True)
    resource_type = wsme.wsattr(wtypes.text)
    resource_uuid = wsme.wsattr(wtypes.text)
    start_time = wsme.wsattr(datetime.datetime)
    fulfill_time = wsme.wsattr(datetime.datetime, readonly=True)
    expire_time = wsme.wsattr(datetime.datetime, readonly=True)
    end_time = wsme.wsattr(datetime.datetime)
    status = wsme.wsattr(wtypes.text, readonly=True)
    properties = {wtypes.text: types.jsontype}
    offer_uuid = wsme.wsattr(wtypes.text, readonly=True)
    offer_uuid_or_name = wsme.wsattr(wtypes.text)

    def __init__(self, **kwargs):
        self.fields = lease_obj.Lease.fields
        for field in self.fields:
            setattr(self, field, kwargs.get(field, wtypes.Unset))


class LeaseCollection(types.Collection):
    leases = [Lease]

    def __init__(self, **kwargs):
        self._type = 'leases'


class LeasesController(rest.RestController):

    @wsme_pecan.wsexpose(Lease, wtypes.text)
    def get_one(self, lease_id):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:lease:get', cdict, cdict)

        permitted = utils.get_lease_authorized(lease_id, cdict)

        return Lease(**permitted.to_dict())

    @wsme_pecan.wsexpose(LeaseCollection, wtypes.text,
                         datetime.datetime, datetime.datetime, wtypes.text,
                         wtypes.text, wtypes.text, wtypes.text,
                         wtypes.text, wtypes.text)
    def get_all(self, project_id=None, start_time=None, end_time=None,
                status=None, offer_uuid=None, view=None, owner_id=None,
                resource_type=None, resource_uuid=None):
        request = pecan.request.context
        cdict = request.to_policy_values()

        if project_id is not None:
            project_id = keystone.get_project_uuid_from_ident(project_id)

        if owner_id is not None:
            owner_id = keystone.get_project_uuid_from_ident(owner_id)

        if resource_uuid is not None:
            if resource_type is None:
                resource_type = CONF.api.default_resource_type
            resource = ro_factory.ResourceObjectFactory.get_resource_object(
                resource_type, resource_uuid)
            resource_uuid = resource.get_resource_uuid()

        filters = LeasesController.\
            _lease_get_all_authorize_filters(
                cdict,
                project_id=project_id, start_time=start_time,
                end_time=end_time, status=status,
                offer_uuid=offer_uuid, view=view, owner_id=owner_id,
                resource_type=resource_type, resource_uuid=resource_uuid)

        lease_collection = LeaseCollection()
        leases = lease_obj.Lease.get_all(filters, request)
        lease_collection.leases = [
            Lease(**lease.to_dict()) for lease in leases]
        return lease_collection

    @wsme_pecan.wsexpose(Lease, body=Lease, status_code=http_client.CREATED)
    def post(self, new_lease):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:lease:create', cdict, cdict)

        lease_dict = new_lease.to_dict()
        lease_dict['owner_id'] = request.project_id
        lease_dict['uuid'] = uuidutils.generate_uuid()
        if 'resource_type' not in lease_dict:
            lease_dict['resource_type'] = CONF.api.default_resource_type

        resource = ro_factory.ResourceObjectFactory.get_resource_object(
            lease_dict['resource_type'], lease_dict['resource_uuid'])
        lease_dict['resource_uuid'] = resource.get_resource_uuid()

        if 'project_id' in lease_dict:
            lease_dict['project_id'] = keystone.get_project_uuid_from_ident(
                lease_dict['project_id'])

        if 'start_time' not in lease_dict:
            lease_dict['start_time'] = datetime.datetime.now()

        if 'end_time' not in lease_dict:
            lease_dict['end_time'] = datetime.datetime.max

        utils.check_resource_admin(cdict,
                                   lease_dict.get('resource_type'),
                                   lease_dict.get('resource_uuid'),
                                   request.project_id,
                                   lease_dict.get('start_time'),
                                   lease_dict.get('end_time'))

        lease = lease_obj.Lease(**lease_dict)
        lease.create(request)
        return Lease(**lease.to_dict())

    @wsme_pecan.wsexpose(Lease, wtypes.text)
    def delete(self, lease_id):
        request = pecan.request.context
        cdict = request.to_policy_values()
        policy.authorize('esi_leap:lease:delete', cdict, cdict)

        permitted = utils.get_lease_authorized(
            lease_id, cdict, [statuses.CREATED, statuses.ACTIVE])

        permitted.cancel()

    @staticmethod
    def _lease_get_all_authorize_filters(cdict,
                                         start_time=None, end_time=None,
                                         status=None, offer_uuid=None,
                                         project_id=None, view=None,
                                         owner_id=None, resource_type=None,
                                         resource_uuid=None):

        if status is None:
            status = [statuses.CREATED, statuses.ACTIVE]
        elif status == 'any':
            status = None
        else:
            status = [status]

        possible_filters = {
            'status': status,
            'offer_uuid': offer_uuid,
            'start_time': start_time,
            'end_time': end_time,
            'resource_type': resource_type,
            'resource_uuid': resource_uuid,
        }

        if view == 'all':
            policy.authorize('esi_leap:lease:lease_admin', cdict, cdict)
            possible_filters['owner_id'] = owner_id
            possible_filters['project_id'] = project_id
        else:
            policy.authorize('esi_leap:lease:get', cdict, cdict)

            if owner_id:
                if cdict['project_id'] != owner_id:
                    policy.authorize('esi_leap:lease:lease_admin',
                                     cdict, cdict)

                possible_filters['owner_id'] = owner_id
                possible_filters['project_id'] = project_id
            else:
                if project_id is None:
                    project_id = cdict['project_id']
                    possible_filters['project_or_owner_id'] = project_id
                else:
                    if project_id != cdict['project_id']:
                        policy.authorize('esi_leap:lease:lease_admin',
                                         cdict, cdict)
                    possible_filters['project_id'] = project_id

        if (start_time and end_time is None) or \
                (end_time and start_time is None):
            raise exception.InvalidTimeAPICommand(resource="a lease",
                                                  start_time=str(start_time),
                                                  end_time=str(end_time))

        if start_time and end_time and\
           end_time <= start_time:
            raise exception.InvalidTimeAPICommand(resource='a lease',
                                                  start_time=str(start_time),
                                                  end_time=str(end_time))

        filters = {}
        for k, v in possible_filters.items():
            if v is not None:
                filters[k] = v

        return filters
