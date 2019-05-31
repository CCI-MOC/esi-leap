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
from esi_leap.db.sqlalchemy import models
from esi_leap.resource_objects import resource_object_factory as ro_factory


CONF = cfg.CONF
LOG = logging.getLogger(__name__)
_engine_facade = None


def get_session():
    global _engine_facade
    if not _engine_facade:
        _engine_facade = db_session.EngineFacade.from_config(CONF)

    return _engine_facade.get_session()


def reset_facade():
    global _engine_facade
    _engine_facade = None


def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]


def setup_db():
    engine = db_session.EngineFacade(CONF.database.connection,
                                     sqlite_fk=True).get_engine()
    models.Base.metadata.create_all(engine)
    return True


def drop_db():
    engine = db_session.EngineFacade(CONF.database.connection,
                                     sqlite_fk=True).get_engine()
    models.Base.metadata.drop_all(engine)
    return True


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


# Leasable Resource
def leasable_resource_get(context, resource_type, resource_uuid):
    query = model_query(context, models.LeasableResource, get_session())
    result = query.filter_by(
        resource_type=resource_type, resource_uuid=resource_uuid).first()
    if not result:
        raise exception.ResourceNotFound(
            resource_type=resource_type, resource_uuid=resource_uuid)
    return result


def leasable_resource_get_all(context):
    query = model_query(context, models.LeasableResource, get_session())
    return query.all()


def leasable_resource_get_all_by_request_project_id(context, project_id):
    query = (model_query(
        context,
        models.LeasableResource,
        get_session()).filter(
            models.LeasableResource.lease_request.has(project_id=project_id)))
    return query.all()


def leasable_resource_get_all_by_request_uuid(context, request_uuid):
    query = (model_query(context, models.LeasableResource,
                         get_session()).filter_by(request_uuid=request_uuid))
    return query.all()


def leasable_resource_get_available(context):
    return leasable_resource_get_all_by_request_uuid(context, None)


def leasable_resource_get_leased(context):
    query = (model_query(context, models.LeasableResource,
                         get_session()).filter(
                             models.LeasableResource.request_uuid is not None))
    return query.all()


def leasable_resource_create(context, values):
    resource_type = values.get('resource_type')
    resource_uuid = values.get('resource_uuid')
    resource = ro_factory.ResourceObjectFactory.get_resource_object(
        resource_type, resource_uuid)
    if not resource.is_resource_admin(context.project_id):
        raise exception.ResourceNoPermission(
            resource_type=resource_type, resource_uuid=resource_uuid)

    leasable_resource_ref = models.LeasableResource()
    leasable_resource_ref.update(values)
    try:
        leasable_resource_ref.save(get_session())
    except db_exception.DBDuplicateEntry:
        raise exception.ResourceExists(
            resource_type=resource_type, resource_uuid=resource_uuid)
    return leasable_resource_ref


def leasable_resource_update(context, resource_type, resource_uuid, values):
    if not context.is_admin:
        resource = ro_factory.ResourceObjectFactory.get_resource_object(
            resource_type, resource_uuid)
        if not resource.is_resource_admin(context.project_id):
            raise exception.ResourceNoPermission(
                resource_type=resource_type, resource_uuid=resource_uuid)

    leasable_resource_ref = leasable_resource_get(
        context, resource_type, resource_uuid)
    leasable_resource_ref.update(values)
    leasable_resource_ref.save(get_session())
    return leasable_resource_ref


def leasable_resource_destroy(context, resource_type, resource_uuid):
    if not context.is_admin:
        resource = ro_factory.ResourceObjectFactory.get_resource_object(
            resource_type, resource_uuid)
        if not resource.is_resource_admin(context.project_id):
            raise exception.ResourceNoPermission(
                resource_type=resource_type, resource_uuid=resource_uuid)
    model_query(context, models.LeasableResource,
                get_session()).filter_by(
                    resource_type=resource_type,
                    resource_uuid=resource_uuid).delete()
