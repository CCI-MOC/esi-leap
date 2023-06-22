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

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy import Index, Integer, String

from esi_leap.common import statuses


@compiles(DateTime, 'mysql')
def compile_datetime_mysql(type_, compiler, **kw):
    return 'DATETIME(6)'


class ESILEAPBase(models.TimestampMixin, models.ModelBase):

    metadata = None

    def to_dict(self):
        d = {}
        for c in self.__table__.columns:
            d[c.name] = self[c.name]
        return d


Base = declarative_base(cls=ESILEAPBase)


class Offer(Base):
    """Represents a resource that is offered."""

    __tablename__ = 'offers'
    __table_args__ = (
        Index('offer_uuid_idx', 'uuid'),
        Index('offer_project_id_idx', 'project_id'),
        Index('offer_resource_idx', 'resource_type', 'resource_uuid'),
        Index('offer_status_idx', 'status'),
    )

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    uuid = Column(String(36), nullable=False, unique=True)
    name = Column(String(35), nullable=True, unique=False)
    project_id = Column(String(255), nullable=False)
    lessee_id = Column(String(255), nullable=True)
    resource_type = Column(String(36), nullable=False)
    resource_uuid = Column(String(36), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String(15), nullable=False, default=statuses.AVAILABLE)
    properties = Column(db_types.JsonEncodedDict, nullable=True)
    parent_lease_uuid = Column(String(36),
                               ForeignKey('leases.uuid'),
                               nullable=True)
    parent_lease = orm.relationship(
        'Lease',
        foreign_keys=[parent_lease_uuid],
    )


class Lease(Base):
    """Represents a lease."""

    __tablename__ = 'leases'
    __table_args__ = (
        Index('lease_uuid_idx', 'uuid'),
        Index('lease_project_id_idx', 'project_id'),
        Index('lease_owner_id_idx', 'owner_id'),
        Index('lease_status_idx', 'status'),
    )

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    uuid = Column(String(36), nullable=False, unique=True)
    name = Column(String(35), nullable=True, unique=False)
    project_id = Column(String(255), nullable=False)
    owner_id = Column(String(255), nullable=False)
    purpose = Column(String(255), nullable=True)
    resource_type = Column(String(36), nullable=False)
    resource_uuid = Column(String(36), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    fulfill_time = Column(DateTime)
    expire_time = Column(DateTime)
    status = Column(String(15), nullable=False, default=statuses.CREATED)
    properties = Column(db_types.JsonEncodedDict, nullable=True)
    offer_uuid = Column(String(36),
                        ForeignKey('offers.uuid'),
                        nullable=True)
    parent_lease_uuid = Column(String(36),
                               ForeignKey('leases.uuid'),
                               nullable=True)
    offer = orm.relationship(
        Offer,
        backref=orm.backref('offers'),
        foreign_keys=offer_uuid,
        primaryjoin=offer_uuid == Offer.uuid)
    parent_lease = orm.relationship(
        'Lease',
        backref=orm.backref('child_leases', remote_side=uuid),
    )


class Event(Base):
    """Represents an event."""

    __tablename__ = 'events'
    __table_args__ = (
        Index('event_type_idx', 'event_type'),
        Index('event_lessee_id_idx', 'lessee_id'),
        Index('event_owner_id_idx', 'owner_id'),
        Index('event_resource_idx', 'resource_type', 'resource_uuid'),
        Index('event_time_idx', 'event_time'),
    )

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    event_type = Column(String(36), nullable=False)
    event_time = Column(DateTime, nullable=False)
    object_type = Column(String(36), nullable=True)
    object_uuid = Column(String(36), nullable=True)
    resource_type = Column(String(36), nullable=True)
    resource_uuid = Column(String(36), nullable=True)
    lessee_id = Column(String(255), nullable=True)
    owner_id = Column(String(255), nullable=True)
