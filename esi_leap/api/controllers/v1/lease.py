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
from esi_leap.api.controllers.v1 import utils
from esi_leap.common import constants
from esi_leap.common import exception
from esi_leap.common import ironic
from esi_leap.common import keystone
from esi_leap.common import statuses
import esi_leap.conf
from esi_leap.objects import lease as lease_obj
from esi_leap.resource_objects import get_resource_object

CONF = esi_leap.conf.CONF


class Lease(base.ESILEAPBase):

    name = wsme.wsattr(wtypes.text)
    uuid = wsme.wsattr(wtypes.text, readonly=True)
    project_id = wsme.wsattr(wtypes.text)
    project = wsme.wsattr(wtypes.text, readonly=True)
    owner_id = wsme.wsattr(wtypes.text, readonly=True)
    owner = wsme.wsattr(wtypes.text, readonly=True)
    resource_type = wsme.wsattr(wtypes.text)
    resource_uuid = wsme.wsattr(wtypes.text)
    resource_class = wsme.wsattr(wtypes.text)
    resource = wsme.wsattr(wtypes.text, readonly=True)
    start_time = wsme.wsattr(datetime.datetime)
    fulfill_time = wsme.wsattr(datetime.datetime, readonly=True)
    expire_time = wsme.wsattr(datetime.datetime, readonly=True)
    end_time = wsme.wsattr(datetime.datetime)
    status = wsme.wsattr(wtypes.text, readonly=True)
    properties = {wtypes.text: types.jsontype}
    purpose = wsme.wsattr(wtypes.text)
    offer_uuid = wsme.wsattr(wtypes.text, readonly=True)
    parent_lease_uuid = wsme.wsattr(wtypes.text, readonly=True)

    def __init__(self, **kwargs):
        self.fields = lease_obj.Lease.fields
        for field in self.fields:
            setattr(self, field, kwargs.get(field, wtypes.Unset))

        for attr in ('project', 'owner', 'resource', 'resource_class'):
            setattr(self, attr, kwargs.get(attr, wtypes.Unset))


class LeaseCollection(types.Collection):
    leases = [Lease]

    def __init__(self, **kwargs):
        self._type = 'leases'


class LeasesController(rest.RestController):

    @wsme_pecan.wsexpose(Lease, wtypes.text)
    def get_one(self, lease_id):
        request = pecan.request.context

        lease = utils.check_lease_policy_and_retrieve(
            request, 'esi_leap:lease:get', lease_id)

        return Lease(**utils.lease_get_dict_with_added_info(lease))

    @wsme_pecan.wsexpose(LeaseCollection, wtypes.text,
                         datetime.datetime, datetime.datetime, wtypes.text,
                         wtypes.text, wtypes.text, wtypes.text,
                         wtypes.text, wtypes.text, wtypes.text)
    def get_all(self, project_id=None, start_time=None, end_time=None,
                status=None, offer_uuid=None, view=None, owner_id=None,
                resource_type=None, resource_uuid=None, resource_class=None):
        request = pecan.request.context
        cdict = request.to_policy_values()

        if project_id is not None:
            project_id = keystone.get_project_uuid_from_ident(project_id)

        if owner_id is not None:
            owner_id = keystone.get_project_uuid_from_ident(owner_id)

        if resource_uuid is not None:
            if resource_type is None:
                resource_type = CONF.api.default_resource_type

            resource = get_resource_object(resource_type, resource_uuid)
            resource_uuid = resource.get_uuid()

        filters = LeasesController._lease_get_all_authorize_filters(
            cdict, project_id=project_id, owner_id=owner_id,
            start_time=start_time, end_time=end_time,
            status=status, offer_uuid=offer_uuid, view=view,
            resource_type=resource_type, resource_uuid=resource_uuid)

        lease_collection = LeaseCollection()
        leases = lease_obj.Lease.get_all(filters, request)

        lease_collection.leases = []

        if len(leases) > 0:
            project_list = None
            node_list = None

            with concurrent.futures.ThreadPoolExecutor() as executor:
                f1 = executor.submit(ironic.get_node_list)
                f2 = executor.submit(keystone.get_project_list)
                node_list = f1.result()
                project_list = f2.result()

            leases_with_added_info = [
                Lease(**utils.lease_get_dict_with_added_info(l, project_list,
                                                             node_list))
                for l in leases]
            if resource_class:
                lease_collection.leases = [
                    l for l in leases_with_added_info
                    if l.resource_class == resource_class]
            else:
                lease_collection.leases = leases_with_added_info

        return lease_collection

    @wsme_pecan.wsexpose(Lease, body=Lease, status_code=http_client.CREATED)
    def post(self, new_lease):
        request = pecan.request.context
        cdict = request.to_policy_values()
        utils.policy_authorize('esi_leap:lease:create', cdict, cdict)

        lease_dict = new_lease.to_dict()
        lease_dict['owner_id'] = request.project_id
        lease_dict['uuid'] = uuidutils.generate_uuid()
        if 'resource_type' not in lease_dict:
            lease_dict['resource_type'] = CONF.api.default_resource_type
        resource = get_resource_object(lease_dict['resource_type'],
                                       lease_dict['resource_uuid'])
        lease_dict['resource_uuid'] = resource.get_uuid()

        if 'project_id' in lease_dict:
            lease_dict['project_id'] = keystone.get_project_uuid_from_ident(
                lease_dict['project_id'])

        if 'start_time' not in lease_dict:
            lease_dict['start_time'] = datetime.datetime.now()

        if 'end_time' not in lease_dict:
            lease_dict['end_time'] = datetime.datetime.max

        try:
            utils.check_resource_admin(cdict, resource, request.project_id)
        except exception.HTTPResourceForbidden:
            parent_lease_uuid = utils.check_resource_lease_admin(
                cdict,
                resource,
                request.project_id,
                lease_dict.get('start_time'),
                lease_dict.get('end_time'))
            if parent_lease_uuid is None:
                raise
            lease_dict['parent_lease_uuid'] = parent_lease_uuid

        lease = lease_obj.Lease(**lease_dict)
        lease.create(request)
        return Lease(**utils.lease_get_dict_with_added_info(lease))

    @wsme_pecan.wsexpose(Lease, wtypes.text)
    def delete(self, lease_id):
        request = pecan.request.context

        lease = utils.check_lease_policy_and_retrieve(
            request, 'esi_leap:lease:get', lease_id,
            statuses.LEASE_CAN_DELETE)

        lease.cancel(request)

    @staticmethod
    def _lease_get_all_authorize_filters(cdict,
                                         start_time=None, end_time=None,
                                         status=None, offer_uuid=None,
                                         project_id=None, view=None,
                                         owner_id=None, resource_type=None,
                                         resource_uuid=None):

        if status is not None:
            status = [status] if status != 'any' else None
        else:
            status = [statuses.CREATED, statuses.ACTIVE, statuses.ERROR,
                      statuses.WAIT_CANCEL, statuses.WAIT_EXPIRE,
                      statuses.WAIT_FULFILL]

        filters = {
            'status': status,
            'offer_uuid': offer_uuid,
            'start_time': start_time,
            'end_time': end_time,
            'resource_type': resource_type,
            'resource_uuid': resource_uuid,
            'time_filter_type': constants.WITHIN_TIME_FILTER,
        }

        if view == 'all':
            utils.policy_authorize('esi_leap:lease:lease_admin', cdict, cdict)
            filters['owner_id'] = owner_id
            filters['project_id'] = project_id
        else:
            utils.policy_authorize('esi_leap:lease:get_all', cdict, cdict)

            if owner_id:
                if cdict['project_id'] != owner_id:
                    utils.policy_authorize('esi_leap:lease:lease_admin', cdict,
                                           cdict)

                filters['owner_id'] = owner_id
                filters['project_id'] = project_id
            else:
                if project_id is None:
                    project_id = cdict['project_id']
                    filters['project_or_owner_id'] = project_id
                else:
                    if project_id != cdict['project_id']:
                        utils.policy_authorize('esi_leap:lease:lease_admin',
                                               cdict, cdict)
                    filters['project_id'] = project_id

        # either both are defined or both are None
        if bool(start_time) != bool(end_time):
            raise exception.InvalidTimeAPICommand(resource='a lease',
                                                  start_time=str(start_time),
                                                  end_time=str(end_time))
        if (start_time or end_time) and (end_time <= start_time):
            raise exception.InvalidTimeAPICommand(resource='a lease',
                                                  start_time=str(start_time),
                                                  end_time=str(end_time))

        # unpack iterator to tuple so we can use 'del'
        for k, v in tuple(filters.items()):
            if v is None:
                del filters[k]

        return filters
