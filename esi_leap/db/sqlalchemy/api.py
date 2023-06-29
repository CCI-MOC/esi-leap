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

import sys
import threading

from oslo_config import cfg
from oslo_db.sqlalchemy import enginefacade
from oslo_log import log as logging

import sqlalchemy as sa
from sqlalchemy import or_

from esi_leap.common import constants
from esi_leap.common import exception
from esi_leap.common import keystone
from esi_leap.common import statuses
from esi_leap.db.sqlalchemy import models


CONF = cfg.CONF
LOG = logging.getLogger(__name__)

_CONTEXT = threading.local()


def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]


def _session_for_read():
    return enginefacade.reader.using(_CONTEXT)


def _session_for_write():
    return enginefacade.writer.using(_CONTEXT)


def model_query(model, *args):
    """Query helper.

    :param model: base model to query
    """
    with _session_for_read() as session:
        query = session.query(model, *args)
        return query


# Helpers for building constraints / equality checks


def constraint(**conditions):
    return Constraint(conditions)


def equal_any(*values):
    return EqualityCondition(values)


def not_equal(*values):
    return InequalityCondition(values)


class Constraint(object):
    def __init__(self, conditions):
        self.conditions = conditions

    def apply(self, model, query):
        for key, condition in self.conditions.items():
            for clause in condition.clauses(getattr(model, key)):
                query = query.filter(clause)
        return query


class EqualityCondition(object):
    def __init__(self, values):
        self.values = values

    def clauses(self, field):
        return sa.or_([field == value for value in self.values])


class InequalityCondition(object):
    def __init__(self, values):
        self.values = values

    def clauses(self, field):
        return [field != value for value in self.values]


# Offer
def offer_get_by_uuid(offer_uuid):
    query = model_query(models.Offer)
    offer_ref = query.filter_by(uuid=offer_uuid).one_or_none()
    return offer_ref


def offer_get_by_name(name):
    query = model_query(models.Offer)
    offers = query.filter_by(name=name).all()
    return offers


def offer_get_all(filters):

    query = model_query(models.Offer)

    lessee_id = filters.pop('lessee_id', None)
    start = filters.pop('start_time', None)
    end = filters.pop('end_time', None)
    time_filter_type = filters.pop('time_filter_type', None)
    a_start = filters.pop('available_start_time', None)
    status = filters.pop('status', None)
    a_end = filters.pop('available_end_time', None)

    query = query.filter_by(**filters)

    if status:
        query = query.filter((models.Offer.status.in_(status)))

    if lessee_id:
        lessee_id_list = keystone.get_parent_project_id_tree(lessee_id)
        query = query.filter(or_(models.Offer.project_id == lessee_id,
                                 models.Offer.lessee_id.__eq__(None),
                                 models.Offer.lessee_id.in_(lessee_id_list)))

    if start and end:
        if time_filter_type == constants.WITHIN_TIME_FILTER:
            query = query.filter(((start <= models.Offer.start_time) &
                                  (end >= models.Offer.start_time)) |

                                 ((start <= models.Offer.end_time) &
                                  (end >= models.Offer.end_time)))
        else:
            query = query.filter((start >= models.Offer.start_time) &
                                 (end <= models.Offer.end_time))

    if a_start and a_end:
        for o in query:
            try:
                offer_verify_availability(o, a_start, a_end)
            except exception.OfferNoTimeAvailabilities:
                query = query.filter(models.Offer.uuid != o.uuid)

    return query


def offer_get_conflict_times(offer_ref):

    l_query = model_query(models.Lease)

    return l_query.with_entities(
        models.Lease.start_time, models.Lease.end_time).\
        join(models.Offer, models.Offer.uuid == models.Lease.offer_uuid).\
        order_by(models.Lease.start_time).\
        filter(models.Lease.offer_uuid == offer_ref.uuid,
               (models.Lease.status != statuses.EXPIRED) &
               (models.Lease.status != statuses.DELETED)
               ).all()


def offer_get_first_availability(offer_uuid, start):
    l_query = model_query(models.Lease)

    return l_query.with_entities(
        models.Lease.start_time).\
        filter(models.Lease.offer_uuid == offer_uuid,
               (models.Lease.status == statuses.CREATED) |
               (models.Lease.status == statuses.ACTIVE)
               ).\
        order_by(models.Lease.start_time).\
        filter(models.Lease.end_time >= start).first()


def offer_verify_availability(offer_ref, start, end):

    if start < offer_ref.start_time or end > offer_ref.end_time:
        raise exception.OfferNoTimeAvailabilities(offer_uuid=offer_ref.uuid,
                                                  start_time=start,
                                                  end_time=end)

    l_query = model_query(models.Lease)

    leases = l_query.with_entities(
        models.Lease.start_time, models.Lease.end_time).\
        filter((models.Lease.offer_uuid == offer_ref.uuid),
               (models.Lease.status == statuses.CREATED) |
               (models.Lease.status == statuses.ACTIVE)
               )
    leases = add_lease_conflict_filter(leases, start, end)
    conflict = leases.first()

    if conflict:
        raise exception.OfferNoTimeAvailabilities(offer_uuid=offer_ref.uuid,
                                                  start_time=start,
                                                  end_time=end)


def offer_create(values):
    offer_ref = models.Offer()
    offer_ref.update(values)

    with _session_for_write() as session:
        session.add(offer_ref)
        session.flush()
        return offer_ref


def offer_update(offer_uuid, values):

    with _session_for_write() as session:

        query = model_query(models.Offer)
        offer_ref = query.filter_by(uuid=offer_uuid).one_or_none()

        values.pop('uuid', None)
        values.pop('project_id', None)

        start = values.get('start_time', None)
        end = values.get('end_time', None)
        if start is None:
            start = offer_ref.start_time
        if end is None:
            end = offer_ref.end_time
        if start >= end:
            raise exception.InvalidTimeRange(resource='an offer',
                                             start_time=str(start),
                                             end_time=str(end))

        offer_ref.update(values)
        session.flush()
        return offer_ref


def offer_destroy(offer_uuid):
    with _session_for_write() as session:
        query = model_query(models.Offer)
        offer_ref = query.filter_by(uuid=offer_uuid).one_or_none()

        if not offer_ref:
            raise exception.OfferNotFound(offer_uuid=offer_uuid)

        model_query(models.Offer).filter_by(uuid=offer_uuid).delete()
        session.flush()


def add_offer_conflict_filter(query, start, end):
    return query.filter((
        ((start >= models.Offer.start_time) &
         (start < models.Offer.end_time)) |

        ((end > models.Offer.start_time) &
         (end <= models.Offer.end_time)) |

        ((start <= models.Offer.start_time) &
         (end >= models.Offer.end_time))
    ))


# Leases
def lease_get_by_uuid(lease_uuid):
    query = model_query(models.Lease)
    result = query.filter_by(uuid=lease_uuid).one_or_none()
    return result


def lease_get_by_name(name):
    query = model_query(models.Lease)
    leases = query.filter_by(name=name).all()
    return leases


def lease_get_all(filters):
    query = model_query(models.Lease)

    start = filters.pop('start_time', None)
    end = filters.pop('end_time', None)
    time_filter_type = filters.pop('time_filter_type', None)
    status = filters.pop('status', None)
    project_or_owner_id = filters.pop('project_or_owner_id', None)

    query = query.filter_by(**filters)

    if status:
        query = query.filter((models.Lease.status.in_(status)))

    if start and end:
        if time_filter_type == constants.WITHIN_TIME_FILTER:
            query = query.filter(((start <= models.Lease.start_time) &
                                  (end >= models.Lease.start_time)) |

                                 ((start <= models.Lease.end_time) &
                                  (end >= models.Lease.end_time)) |

                                 ((start >= models.Lease.start_time) &
                                  (end <= models.Lease.end_time)))

        else:
            query = query.filter((start >= models.Lease.start_time) &
                                 (end <= models.Lease.end_time))

    if project_or_owner_id:
        query = query.filter(
            (project_or_owner_id == models.Lease.project_id) |
            (project_or_owner_id == models.Lease.owner_id))

    return query


def lease_create(values):
    lease_ref = models.Lease()
    lease_ref.update(values)

    with _session_for_write() as session:
        session.add(lease_ref)
        session.flush()
        return lease_ref


def lease_update(lease_uuid, values):
    with _session_for_write() as session:
        query = model_query(models.Lease)
        lease_ref = query.filter_by(uuid=lease_uuid).one_or_none()

        values.pop('uuid', None)
        values.pop('project_id', None)

        start = values.get('start_time', None)
        end = values.get('end_time', None)
        if start is None:
            start = lease_ref.start_time
        if end is None:
            end = lease_ref.end_time
        if start >= end:
            raise exception.InvalidTimeRange(resource='a lease',
                                             start_time=str(start),
                                             end_time=str(end))

        lease_ref.update(values)
        session.flush()
        return lease_ref


def lease_destroy(lease_uuid):
    with _session_for_write() as session:

        query = model_query(models.Lease)
        lease_ref = query.filter_by(uuid=lease_uuid).one_or_none()

        if not lease_ref:
            raise exception.LeaseNotFound(lease_uuid=lease_uuid)
        query.delete()
        session.flush()


def lease_verify_child_availability(lease_ref, start, end):
    if start < lease_ref.start_time or end > lease_ref.end_time:
        raise exception.LeaseNoTimeAvailabilities(lease_uuid=lease_ref.uuid,
                                                  start_time=start,
                                                  end_time=end)

    # check lease conflicts
    l_query = model_query(models.Lease)
    leases = l_query.with_entities(
        models.Lease.start_time, models.Lease.end_time).\
        filter((models.Lease.parent_lease_uuid == lease_ref.uuid),
               (models.Lease.status == statuses.CREATED) |
               (models.Lease.status == statuses.ACTIVE)
               )
    leases = add_lease_conflict_filter(leases, start, end)
    lease_conflict = leases.first()

    if lease_conflict:
        raise exception.LeaseNoTimeAvailabilities(lease_uuid=lease_ref.uuid,
                                                  start_time=start,
                                                  end_time=end)

    # check offer conflicts
    o_query = model_query(models.Offer)
    offers = o_query.with_entities(
        models.Offer.start_time, models.Offer.end_time).\
        filter((models.Offer.parent_lease_uuid == lease_ref.uuid),
               (models.Offer.status == statuses.AVAILABLE))
    offers = add_offer_conflict_filter(offers, start, end)
    offer_conflict = offers.first()

    if offer_conflict:
        raise exception.LeaseNoTimeAvailabilities(lease_uuid=lease_ref.uuid,
                                                  start_time=start,
                                                  end_time=end)


def add_lease_conflict_filter(query, start, end):
    return query.filter((
        ((start >= models.Lease.start_time) &
         (start < models.Lease.end_time)) |

        ((end > models.Lease.start_time) &
         (end <= models.Lease.end_time)) |

        ((start <= models.Lease.start_time) &
         (end >= models.Lease.end_time))
    ))


# Resources
def resource_verify_availability(r_type, r_uuid, start, end):
    # check conflict with offers
    o_query = model_query(models.Offer)

    offers = o_query.with_entities(
        models.Offer.start_time, models.Offer.end_time).\
        filter((models.Offer.resource_uuid == r_uuid),
               (models.Offer.resource_type == r_type),
               (models.Offer.status == statuses.AVAILABLE))
    offers = add_offer_conflict_filter(offers, start, end)
    offer_conflict = offers.first()

    if offer_conflict:
        raise exception.ResourceTimeConflict(
            resource_uuid=r_uuid,
            resource_type=r_type)

    # check conflict with leases
    l_query = model_query(models.Lease)

    leases = l_query.with_entities(
        models.Lease.start_time, models.Lease.end_time).\
        filter((models.Lease.resource_uuid == r_uuid),
               (models.Lease.resource_type == r_type),
               (models.Lease.status.in_([statuses.CREATED, statuses.ACTIVE])))
    leases = add_lease_conflict_filter(leases, start, end)
    lease_conflict = leases.first()

    if lease_conflict:
        raise exception.ResourceTimeConflict(
            resource_uuid=r_uuid,
            resource_type=r_type)


# Events

def event_get_all(filters):
    query = model_query(models.Event)

    last_event_time = filters.pop('last_event_time', None)
    last_event_id = filters.pop('last_event_id', None)
    lessee_or_owner_id = filters.pop('lessee_or_owner_id', None)

    query = query.filter_by(**filters)

    if last_event_time:
        query = query.filter(
            last_event_time < models.Event.event_time)
    if last_event_id:
        query = query.filter(last_event_id < models.Event.id)
    if lessee_or_owner_id:
        query = query.filter(
            (lessee_or_owner_id == models.Event.lessee_id) |
            (lessee_or_owner_id == models.Event.owner_id))

    return query


def event_create(values):
    event_ref = models.Event()
    event_ref.update(values)

    with _session_for_write() as session:
        session.add(event_ref)
        session.flush()
        return event_ref
