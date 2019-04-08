import sys

from oslo_config import cfg
from oslo_db import exception as common_db_exc
from oslo_db.sqlalchemy import session as db_session
from oslo_log import log as logging
from oslo_utils import uuidutils

import sqlalchemy as sa
from sqlalchemy.sql.expression import asc
from sqlalchemy.sql.expression import desc

from blazar.db import exceptions as db_exc
from blazar.db.sqlalchemy import facade_wrapper
from esi_leap.db.sqlalchemy import models


LOG = logging.getLogger(__name__)

get_engine = facade_wrapper.get_engine
get_session = facade_wrapper.get_session


def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]


def model_query(context, model, session=None):
    """Query helper.

    :param model: base model to query
    """
    session = session or get_session()

    return session.query(model)


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


# Policy
def policy_get(context, policy_uuid):
    query = model_query(context, models.Policy, get_session())
    return query.filter_by(uuid=policy_uuid).first()


def policy_get_all(context):
    query = model_query(context, models.Policy, get_session())
    return query.all()


def policy_get_all_by_project_id(context, project_id):
    query = (model_query(context, models.Policy,
                         get_session()).filter_by(project_id=project_id))
    return query.all()


def policy_create(context, values):
    policy_ref = models.Policy()
    policy_ref['uuid'] = uuidutils.generate_uuid()
    policy_ref.update(values)
    policy_ref.save(get_session())
    return policy_ref


def policy_update(context, policy_uuid, values):
    policy_ref = policy_get(context, policy_uuid)
    policy_ref.update(values)
    policy_ref.save(get_session())
    return policy_ref


def policy_destroy(context, policy_uuid):
    policy_get(context, policy_uuid).delete()


# Applied Policy
def applied_policy_get(context, node_uuid, policy_uuid):
    query = model_query(context, models.AppliedPolicy, get_session())
    return query.filter_by(node_uuid=node_uuid).filter_by(policy_uuid=policy_uuid).first()


def applied_policy_get_all(context):
    query = model_query(context, models.AppliedPolicy, get_session())
    return query.all()


def applied_policy_get_all_by_project_id(context, project_id):
    query = (model_query(context, models.AppliedPolicy,
                         get_session()).filter_by(models.AppliedPolicy.policy.has(project_id=project_id)))
    return query.all()


def applied_policy_create(context, values):
    applied_policy_ref = models.Policy()
    applied_policy_ref.update(values)
    applied_policy_ref.save(get_session())
    return applied_policy_ref

def applied_policy_update(context, node_uuid, policy_uuid, values):
    applied_policy_ref = applied_policy_get(context, node_uuid, policy_uuid)
    applied_policy_ref.update(values)
    applied_policy_ref.save(get_session())
    return applied_policy_ref


def applied_policy_destroy(context, node_uuid, policy_uuid):
    applied_policy_get(context, node_uuid, policy_uuid).delete()


# Lease Request
def lease_request_get(context, request_uuid):
    query = model_query(context, models.LeaseRequest, get_session())
    return query.filter_by(uuid=request_uuid).first()


def lease_request_get_all(context):
    query = model_query(context, models.LeaseRequest, get_session())
    return query.all()


def lease_request_get_all_by_project_id(context, project_id):
    query = (model_query(context, models.LeaseRequest,
                         get_session()).filter_by(project_id=project_id))
    return query.all()


def lease_request_create(context, values):
    lease_request_ref = models.LeaseRequest()
    lease_request_ref['uuid'] = uuidutils.generate_uuid()
    lease_request_ref.update(values)
    lease_request_ref.save(get_session())
    return lease_request_ref


def lease_request_update(context, request_uuid, values):
    lease_request_ref = lease_request_get(context, request_uuid)
    lease_request_ref.update(values)
    lease_request_ref.save(get_session())
    return lease_request_ref


def lease_request_destroy(context, request_uuid):
    lease_request_get(context, request_uuid).delete()


# Leased Node
def leased_node_get(context, node_uuid):
    query = model_query(context, models.LeasedNode, get_session())
    return query.filter_by(node_uuid=node_uuid).first()


def leased_node_get_all(context):
    query = model_query(context, models.LeasedNode, get_session())
    return query.all()


def leased_node_get_all_by_request_uuid(context, request_uuid):
    query = (model_query(context, models.LeasedNode,
                         get_session()).filter_by(request_uuid=request_id))
    return query.all()


def leased_node_get_all_by_project_id(context, project_id):
    query = (model_query(context, models.LeasedNode,
                         get_session()).filter_by(models.LeasedNode.lease_request.has(project_id=project_id)))
    return query.all()


def leased_node_create(context, values):
    leased_node_ref = models.LeasedNode()
    leased_node_ref.update(values)
    leased_node_ref.save(get_session())
    return leased_node_ref


def leased_node_update(context, node_uuid, values):
    leased_node_ref = leased_node_get(context, node_uuid)
    leased_node_ref.update(values)
    leased_node_ref.save(get_session())
    return leased_node_ref


def leased_node_destroy(context, node_uuid):
    leased_node_get(context, node_uuid).delete()
