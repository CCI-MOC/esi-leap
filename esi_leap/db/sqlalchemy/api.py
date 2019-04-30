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

from oslo_config import cfg
from oslo_db import exception as db_exception
from oslo_db.sqlalchemy import session as db_session
from oslo_log import log as logging
from oslo_utils import uuidutils

import sqlalchemy as sa

from esi_leap.common import exception
from esi_leap.common import ironic
from esi_leap.db.sqlalchemy import models


CONF = cfg.CONF
LOG = logging.getLogger(__name__)
_engine_facade = None


def get_session():
    global _engine_facade
    if not _engine_facade:
        _engine_facade = db_session.EngineFacade.from_config(CONF)

    return _engine_facade.get_session()


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
    result = query.filter_by(uuid=policy_uuid).first()
    if not result:
        raise exception.PolicyNotFound(policy_uuid=policy_uuid)
    if not context.is_admin:
        if context.project_id != result.project_id:
            raise exception.PolicyNoPermission(policy_uuid=policy_uuid)
    return result


def policy_get_all(context):
    if not context.is_admin:
        return policy_get_all_by_project_id(context, context.project_id)

    query = model_query(context, models.Policy, get_session())
    return query.all()


def policy_get_all_by_project_id(context, project_id):
    if not context.is_admin:
        if context.project_id != project_id:
            raise exception.ProjectNoPermission(project_id=project_id)

    query = (model_query(context, models.Policy,
                         get_session()).filter_by(project_id=project_id))
    return query.all()


def policy_create(context, values):
    policy_ref = models.Policy()
    values['uuid'] = uuidutils.generate_uuid()
    values['project_id'] = context.project_id
    policy_ref.update(values)
    policy_ref.save(get_session())
    return policy_ref


def policy_update(context, policy_uuid, values):
    policy_ref = policy_get(context, policy_uuid)
    if not context.is_admin:
        if context.project_id != policy_ref.project_id:
            raise exception.PolicyNoPermission(policy_uuid=policy_uuid)
    values.pop('uuid', None)
    values.pop('project_id', None)
    policy_ref.update(values)
    policy_ref.save(get_session())
    return policy_ref


def policy_destroy(context, policy_uuid):
    policy_ref = policy_get(context, policy_uuid)
    if not policy_ref:
        raise exception.PolicyNotFound(policy_uuid=policy_uuid)
    if not context.is_admin:
        if context.project_id != policy_ref.project_id:
            raise exception.PolicyNoPermission(policy_uuid=policy_uuid)
    model_query(
        context,
        models.Policy,
        get_session()).filter_by(uuid=policy_uuid).delete()


# Lease Request
def lease_request_get(context, request_uuid):
    query = model_query(context, models.LeaseRequest, get_session())
    result = query.filter_by(uuid=request_uuid).first()
    if not result:
        raise exception.LeaseRequestNotFound(request_uuid=request_uuid)
    if not context.is_admin:
        if context.project_id != result.project_id:
            raise exception.LeaseRequestNoPermission(request_uuid=request_uuid)
    return result


def lease_request_get_all(context):
    if not context.is_admin:
        return lease_request_get_all_by_project_id(context, context.project_id)
    query = model_query(context, models.LeaseRequest, get_session())
    return query.all()


def lease_request_get_all_by_project_id(context, project_id):
    if not context.is_admin:
        if context.project_id != project_id:
            raise exception.ProjectNoPermission(project_id=project_id)

    query = (model_query(context, models.LeaseRequest,
                         get_session()).filter_by(project_id=project_id))
    return query.all()


def lease_request_get_all_by_status(context, status):
    query = (model_query(context, models.LeaseRequest,
                         get_session()).filter_by(status=status))
    if not context.is_admin:
        query.filter_by(project_id=context.project_id)
    return query.all()


def lease_request_create(context, values):
    lease_request_ref = models.LeaseRequest()
    values['uuid'] = uuidutils.generate_uuid()
    values['project_id'] = context.project_id
    lease_request_ref.update(values)
    lease_request_ref.save(get_session())
    return lease_request_ref


def lease_request_update(context, request_uuid, values):
    lease_request_ref = lease_request_get(context, request_uuid)
    if not context.is_admin:
        if context.project_id != lease_request_ref.project_id:
            raise exception.LeaseRequestNoPermission(request_uuid=request_uuid)
    values.pop('uuid', None)
    values.pop('project_id', None)
    lease_request_ref.update(values)
    lease_request_ref.save(get_session())
    return lease_request_ref


def lease_request_destroy(context, request_uuid):
    lease_request_ref = lease_request_get(context, request_uuid)
    if not lease_request_ref:
        raise exception.LeaseRequestNotFound(request_uuid=request_uuid)
    if not context.is_admin:
        if context.project_id != lease_request_ref.project_id:
            raise exception.LeaseRequestNoPermission(request_uuid=request_uuid)
    model_query(
        context,
        models.LeaseRequest,
        get_session()).filter_by(uuid=request_uuid).delete()


# Policy Node
def policy_node_get(context, node_uuid):
    query = model_query(context, models.PolicyNode, get_session())
    result = query.filter_by(node_uuid=node_uuid).first()
    if not result:
        raise exception.NodeNotFound(node_uuid=node_uuid)
    return result


def policy_node_get_all(context):
    query = model_query(context, models.PolicyNode, get_session())
    return query.all()


def policy_node_get_all_by_project_id(context, project_id):
    query = (model_query(
        context,
        models.PolicyNode,
        get_session()).filter(
            models.PolicyNode.policy.has(project_id=project_id)))
    return query.all()


def policy_node_get_all_by_request_project_id(context, project_id):
    query = (model_query(
        context,
        models.PolicyNode,
        get_session()).filter(
            models.PolicyNode.lease_request.has(project_id=project_id)))
    return query.all()


def policy_node_get_all_by_policy_uuid(context, policy_uuid):
    query = (model_query(context, models.PolicyNode,
                         get_session()).filter_by(policy_uuid=policy_uuid))
    return query.all()


def policy_node_get_all_by_request_uuid(context, request_uuid):
    query = (model_query(context, models.PolicyNode,
                         get_session()).filter_by(request_uuid=request_uuid))
    return query.all()


def policy_node_get_available(context):
    return policy_node_get_all_by_request_uuid(context, None)


def policy_node_create(context, values):
    node_uuid = values.get('node_uuid')
    if ironic.get_node_project_owner_id(node_uuid) != context.project_id:
        raise exception.NodeNoPermission(node_uuid=node_uuid)

    policy_node_ref = models.PolicyNode()
    policy_node_ref.update(values)
    try:
        policy_node_ref.save(get_session())
    except db_exception.DBDuplicateEntry:
        raise exception.NodeExists(node_uuid=node_uuid)
    return policy_node_ref


def policy_node_update(context, node_uuid, values):
    if not context.is_admin:
        if ironic.get_node_project_owner_id(node_uuid) != context.project_id:
            raise exception.NodeNoPermission(node_uuid=node_uuid)

    policy_node_ref = policy_node_get(context, node_uuid)
    policy_node_ref.update(values)
    policy_node_ref.save(get_session())
    return policy_node_ref


def policy_node_destroy(context, node_uuid):
    if not context.is_admin:
        if ironic.get_node_project_owner_id(node_uuid) != context.project_id:
            raise exception.NodeNoPermission(node_uuid=node_uuid)

    model_query(context, models.PolicyNode,
                get_session()).filter_by(node_uuid=node_uuid).delete()
