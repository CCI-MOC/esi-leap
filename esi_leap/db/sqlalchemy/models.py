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

from oslo_db.sqlalchemy import models
from oslo_db.sqlalchemy import types as db_types

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from sqlalchemy import Column, ForeignKey, DateTime
from sqlalchemy import Boolean, Index, Integer, String

from esi_leap.common import statuses


class ESILEAPBase(models.TimestampMixin, models.ModelBase):

    metadata = None

    def to_dict(self):
        d = {}
        for c in self.__table__.columns:
            d[c.name] = self[c.name]
        return d


Base = declarative_base(cls=ESILEAPBase)


class Policy(Base):
    """Represents a policy that can be applied to a node."""

    __tablename__ = 'policies'
    __table_args__ = (
        Index('project_id_idx', 'project_id'),
        Index('uuid_idx', 'uuid'),
    )

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    uuid = Column(String(36), nullable=False, unique=True)
    project_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    max_time_for_lease = Column(Integer, default=0)
    extendible = Column(Boolean, default=False)


class LeaseRequest(Base):
    """Represents a lease request."""

    __tablename__ = 'lease_requests'
    __table_args__ = (
        Index('project_id_idx', 'project_id'),
        Index('uuid_idx', 'uuid'),
        Index('status_idx', 'status'),
    )

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    uuid = Column(String(36), nullable=True, unique=True)
    project_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    node_properties = Column(db_types.JsonEncodedDict, nullable=True)
    min_nodes = Column(Integer, default=0)
    max_nodes = Column(Integer, default=0)
    lease_time = Column(Integer, default=0)
    status = Column(String(15), nullable=False, default=statuses.PENDING)
    cancel_date = Column(DateTime, nullable=True)
    fulfilled_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)


class PolicyNode(Base):
    """Represents a node that has a policy applied to it."""

    __tablename__ = 'policy_nodes'
    __table_args__ = (
        Index('node_uuid_idx', 'node_uuid'),
        Index('policy_uuid_idx', 'policy_uuid'),
        Index('request_uuid_idx', 'request_uuid'),
    )

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    node_uuid = Column(String(36), nullable=False, unique=True)
    policy_uuid = Column(String(36),
                         ForeignKey('policies.uuid'),
                         nullable=False)
    expiration_date = Column(DateTime)
    request_uuid = Column(String(36),
                          ForeignKey('lease_requests.uuid'),
                          nullable=True)
    lease_expiration_date = Column(DateTime)

    policy = orm.relationship(Policy,
                              backref=orm.backref('applied_nodes'),
                              foreign_keys=policy_uuid,
                              primaryjoin=policy_uuid == Policy.uuid)
    lease_request = orm.relationship(
        LeaseRequest,
        backref=orm.backref('leases'),
        foreign_keys=request_uuid,
        primaryjoin=request_uuid == LeaseRequest.uuid)
