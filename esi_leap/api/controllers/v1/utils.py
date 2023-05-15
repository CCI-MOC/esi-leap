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
from esi_leap.common import keystone
from esi_leap.common import policy
from esi_leap.objects import lease as lease_obj
from esi_leap.objects import offer as offer_obj


def check_resource_admin(cdict, resource, project_id):
    if project_id != resource.get_owner_project_id():
        resource_policy_authorize('esi_leap:offer:offer_admin',
                                  cdict, cdict,
                                  resource.resource_type,
                                  resource.get_uuid())


def check_resource_lease_admin(cdict, resource, project_id,
                               start_time, end_time):
    # check to see if project is current lessee
    if project_id == resource.get_lessee_project_id():
        parent_lease_uuid = resource.get_lease_uuid()
        if parent_lease_uuid is not None:
            parent_lease = lease_obj.Lease.get(parent_lease_uuid)

            # don't allow sub-sub-leases
            if parent_lease.parent_lease_uuid is None:
                # check if offer is within start and end time bounds
                if ((start_time >= parent_lease.start_time) and
                        (end_time <= parent_lease.end_time)):
                    return parent_lease_uuid
                else:
                    raise exception.ResourceNoPermissionTime(
                        resource_type=resource.resource_type,
                        resource_uuid=resource.get_uuid(),
                        start_time=start_time,
                        end_time=end_time)


def get_offer(uuid_or_name, status_filters=[]):
    if uuidutils.is_uuid_like(uuid_or_name):
        o = offer_obj.Offer.get(uuid_or_name)
        if not status_filters or o.status in status_filters:
            return o
        else:
            raise exception.OfferNotFound(offer_uuid=uuid_or_name)
    else:
        offers = offer_obj.Offer.get_all({'name': uuid_or_name,
                                          'status': status_filters})

        if len(offers) != 1:
            if len(offers) == 0:
                raise exception.OfferNotFound(offer_uuid=uuid_or_name)
            else:
                raise exception.OfferDuplicateName(name=uuid_or_name)

        return offers[0]


def get_lease(uuid_or_name, status_filters=[]):
    if uuidutils.is_uuid_like(uuid_or_name):
        lease = lease_obj.Lease.get(uuid_or_name)
        if not status_filters or lease.status in status_filters:
            return lease
        else:
            raise exception.LeaseNotFound(lease_id=uuid_or_name)
    else:
        leases = lease_obj.Lease.get_all({'name': uuid_or_name,
                                          'status': status_filters})

        if len(leases) != 1:
            if len(leases) == 0:
                raise exception.LeaseNotFound(lease_id=uuid_or_name)
            else:
                raise exception.LeaseDuplicateName(name=uuid_or_name)

        return leases[0]


def policy_authorize(policy_name, target, creds):
    try:
        policy.authorize(policy_name, target, creds)
    except oslo_policy.PolicyNotAuthorized:
        raise exception.HTTPForbidden(rule=policy_name)


def resource_policy_authorize(policy_name, target, creds,
                              resource_type, resource):
    try:
        policy_authorize(policy_name, target, creds)
    except exception.HTTPForbidden:
        raise exception.HTTPResourceForbidden(resource_type=resource_type,
                                              resource=resource)


def check_lease_policy_and_retrieve(request, policy_name, lease_ident,
                                    status_filters=[]):
    lease = get_lease(lease_ident, status_filters)

    cdict = request.to_policy_values()
    target = dict(cdict)
    target['lease.owner_id'] = lease.owner_id
    target['lease.project_id'] = lease.project_id

    resource_policy_authorize(policy_name, target, cdict, 'lease', lease.uuid)
    return lease


def check_offer_policy_and_retrieve(request, policy_name, offer_ident,
                                    status_filters=[]):
    offer = get_offer(offer_ident, status_filters)

    cdict = request.to_policy_values()
    target = dict(cdict)
    target['offer.project_id'] = offer.project_id

    resource_policy_authorize(policy_name, target, cdict, 'offer', offer.uuid)
    return offer


def check_offer_lessee(cdict, offer):
    project_id = cdict['project_id']

    # pass if offer has no lessee limitation or project_id created the offer
    if offer.lessee_id is None or offer.project_id == project_id:
        return

    if offer.lessee_id not in keystone.get_parent_project_id_tree(project_id):
        resource_policy_authorize(
            'esi_leap:offer:offer_admin',
            cdict, cdict, 'offer', offer.uuid)


def offer_get_dict_with_added_info(offer, project_list=None, node_list=None):
    resource = offer.resource_object()

    o = offer.to_dict()
    o['availabilities'] = offer.get_availabilities()
    o['project'] = keystone.get_project_name(offer.project_id, project_list)
    o['lessee'] = keystone.get_project_name(offer.lessee_id, project_list)
    o['resource'] = resource.get_name(node_list)
    o['resource_class'] = resource.get_resource_class(node_list)
    return o


def lease_get_dict_with_added_info(lease, project_list=None, node_list=None):
    resource = lease.resource_object()

    lease_dict = lease.to_dict()
    lease_dict['project'] = keystone.get_project_name(lease.project_id,
                                                      project_list)
    lease_dict['owner'] = keystone.get_project_name(lease.owner_id,
                                                    project_list)
    lease_dict['resource'] = resource.get_name(node_list)
    lease_dict['resource_class'] = resource.get_resource_class(node_list)
    return lease_dict
