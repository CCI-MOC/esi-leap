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
from oslo_db import options as db_options
from oslo_log import log as logging


_BACKEND_MAPPING = {
    'sqlalchemy': 'esi_leap.db.sqlalchemy.api',
}

db_options.set_defaults(cfg.CONF)
IMPL = db_api.DBAPI(cfg.CONF.database.backend,
                    backend_mapping=_BACKEND_MAPPING)
LOG = logging.getLogger(__name__)


def get_instance():
    """Return a DB API instance."""
    return IMPL


def setup_db():
    """Set up database, create tables, etc.

    Return True on success, False otherwise
    """
    return IMPL.setup_db()


def drop_db():
    """Drop database.

    Return True on success, False otherwise
    """
    return IMPL.drop_db()


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

        if isinstance(res, list):
            return [item.to_dict() for item in res]

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


def offer_verify_contract_availability(offer_ref, start, end):
    return IMPL.offer_verify_contract_availability(
        offer_ref, start, end)


def offer_verify_resource_availability(r_type, r_uuid, start, end):
    return IMPL.offer_verify_resource_availability(
        r_type, r_uuid, start, end)


def offer_create(values):
    return IMPL.offer_create(values)


def offer_update(context, offer_uuid, values):
    return IMPL.offer_update(context, offer_uuid, values)


def offer_destroy(offer_uuid):
    return IMPL.offer_destroy(offer_uuid)


# Contract
@to_dict
def contract_get_by_uuid(contract_uuid):
    return IMPL.contract_get(contract_uuid)


@to_dict
def contract_get_by_name(contract_name):
    return IMPL.contract_get(contract_name)


@to_dict
def contract_get_all():
    return IMPL.contract_get_all()


def contract_create(values):
    return IMPL.contract_create(values)


def contract_update(contract_uuid, values):
    return IMPL.contract_update(contract_uuid, values)


def contract_destroy(contract_uuid):
    return IMPL.contract_destroy(contract_uuid)
