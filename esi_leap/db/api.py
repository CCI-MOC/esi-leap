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

from oslo_config import cfg
from oslo_db import api as db_api
from oslo_log import log as logging


_BACKEND_MAPPING = {
    'sqlalchemy': 'esi_leap.db.sqlalchemy.api',
}

IMPL = db_api.DBAPI.from_config(cfg.CONF,
                                backend_mapping=_BACKEND_MAPPING,
                                lazy=True)
LOG = logging.getLogger(__name__)


def get_instance():
    """Return a DB API instance."""
    return IMPL


# Helpers for building constraints / equality checks


def constraint(**conditions):
    """Return a constraint object suitable for use with some updates."""
    return IMPL.constraint(**conditions)


def equal_any(*values):
    """Return an equality condition object suitable for use in a constraint.

    Equal_any conditions require that a model object's attribute equal any
    one of the given values.
    """
    return IMPL.equal_any(*values)


def not_equal(*values):
    """Return an inequality condition object suitable for use in a constraint.

    Not_equal conditions require that a model object's attribute differs from
    all of the given values.
    """
    return IMPL.not_equal(*values)


def to_dict(func):
    def decorator(*args, **kwargs):
        res = func(*args, **kwargs)

        try:
            return [item.to_dict() for item in res]
        except (AttributeError, TypeError):
            if res:
                return res.to_dict()
            else:
                return None

    return decorator


# Offer
@to_dict
def offer_get_by_uuid(offer_uuid):
    return IMPL.offer_get_by_uuid(offer_uuid)


@to_dict
def offer_get_by_name(offer_name):
    return IMPL.offer_get(offer_name)


@to_dict
def offer_get_all():
    return IMPL.offer_get_all()


@to_dict
def offer_get_conflict_times(offer_ref):
    return IMPL.offer_get_conflict_times(offer_ref)


def offer_get_first_availability(offer_uuid, start, end):
    return IMPL.offer_get_first_availability(
        offer_uuid, start, end)


def offer_verify_availability(offer_ref, start, end):
    return IMPL.offer_verify_availability(
        offer_ref, start, end)


def offer_create(values):
    return IMPL.offer_create(values)


def offer_update(context, offer_uuid, values):
    return IMPL.offer_update(context, offer_uuid, values)


def offer_destroy(offer_uuid):
    return IMPL.offer_destroy(offer_uuid)


# Lease
@to_dict
def lease_get_by_uuid(lease_uuid):
    return IMPL.lease_get(lease_uuid)


@to_dict
def lease_get_by_name(lease_name):
    return IMPL.lease_get(lease_name)


@to_dict
def lease_get_all():
    return IMPL.lease_get_all()


def lease_create(values):
    return IMPL.lease_create(values)


def lease_update(lease_uuid, values):
    return IMPL.lease_update(lease_uuid, values)


def lease_destroy(lease_uuid):
    return IMPL.lease_destroy(lease_uuid)


def lease_verify_child_availability(lease_ref, start, end):
    return IMPL.lease_verify_child_availability(
        lease_ref, start, end)


# Resource object
def resource_verify_availability(r_type, r_uuid, start, end):
    return IMPL.resource_verify_availability(
        r_type, r_uuid, start, end)


def resource_check_admin(resource_type, resource_uuid,
                         start_time, end_time,
                         default_admin_project_id, project_id):
    return IMPL.resource_check_admin(
        resource_type, resource_uuid, start_time, end_time,
        default_admin_project_id, project_id)


# Event
@to_dict
def event_get_all():
    return IMPL.event_get_all()


def event_create(values):
    return IMPL.event_create(values)
