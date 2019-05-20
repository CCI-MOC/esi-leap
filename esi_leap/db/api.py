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


# Policy
@to_dict
def policy_get(context, policy_uuid):
    return IMPL.policy_get(context, policy_uuid)


@to_dict
def policy_get_all(context):
    return IMPL.policy_get_all(context)


@to_dict
def policy_get_all_by_project_id(context, project_id):
    return IMPL.policy_get_all_by_project_id(context, project_id)


def policy_create(context, values):
    return IMPL.policy_create(context, values)


def policy_update(context, policy_uuid, values):
    return IMPL.policy_update(context, policy_uuid, values)


def policy_destroy(context, policy_uuid):
    IMPL.policy_destroy(context, policy_uuid)


# Lease Request
@to_dict
def lease_request_get(context, request_uuid):
    return IMPL.lease_request_get(context, request_uuid)


@to_dict
def lease_request_get_all(context):
    return IMPL.lease_request_get_all(context)


@to_dict
def lease_request_get_all_by_project_id(context, project_id):
    return IMPL.lease_request_get_all_by_project_id(context, project_id)


@to_dict
def lease_request_get_all_by_status(context, status):
    return IMPL.lease_request_get_all_by_status(context, status)


def lease_request_create(context, values):
    return IMPL.lease_request_create(context, values)


def lease_request_update(context, request_uuid, values):
    return IMPL.lease_request_update(context, request_uuid, values)


def lease_request_destroy(context, request_uuid):
    return IMPL.lease_request_destroy(context, request_uuid)


# Policy Node
@to_dict
def leasable_resource_get(context, node_uuid):
    return IMPL.leasable_resource_get(context, node_uuid)


@to_dict
def leasable_resource_get_all(context):
    return IMPL.leasable_resource_get_all(context)


@to_dict
def leasable_resource_get_all_by_project_id(context, project_id):
    return IMPL.leasable_resource_get_all_by_project_id(context, project_id)


@to_dict
def leasable_resource_get_all_by_request_project_id(context, project_id):
    return IMPL.leasable_resource_get_all_by_request_project_id(
        context, project_id)


@to_dict
def leasable_resource_get_all_by_policy_uuid(context, policy_uuid):
    return IMPL.leasable_resource_get_all_by_policy_uuid(context, policy_uuid)


@to_dict
def leasable_resource_get_all_by_request_uuid(context, request_uuid):
    return IMPL.leasable_resource_get_all_by_policy_uuid(context, request_uuid)


@to_dict
def leasable_resource_get_available(context):
    return IMPL.leasable_resource_get_available(context)


@to_dict
def leasable_resource_get_leased(context):
    return IMPL.leasable_resource_get_leased(context)


def leasable_resource_create(context, values):
    return IMPL.leasable_resource_create(context, values)


def leasable_resource_update(context, node_uuid, values):
    return IMPL.leasable_resource_update(context, node_uuid, values)


def leasable_resource_destroy(context, node_uuid):
    IMPL.leasable_resource_destroy(context, node_uuid)
