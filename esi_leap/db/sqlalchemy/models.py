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
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy import Index, Integer, String

from esi_leap.common import statuses


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
    project_id = Column(String(255), nullable=False)
    resource_type = Column(String(36), nullable=False)
    resource_uuid = Column(String(36), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String(15), nullable=False, default=statuses.AVAILABLE)
    properties = Column(db_types.JsonEncodedDict, nullable=True)


class Contract(Base):
    """Represents an accepted contract."""

    __tablename__ = 'contracts'
    __table_args__ = (
        Index('contract_uuid_idx', 'uuid'),
        Index('contract_project_id_idx', 'project_id'),
        Index('contract_status_idx', 'status'),
    )

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    uuid = Column(String(36), nullable=False, unique=True)
    project_id = Column(String(255), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String(15), nullable=False, default=statuses.OPEN)
    properties = Column(db_types.JsonEncodedDict, nullable=True)
    offer_uuid = Column(String(36),
                        ForeignKey('offers.uuid'),
                        nullable=False)
    offer = orm.relationship(
        Offer,
        backref=orm.backref('offers'),
        foreign_keys=offer_uuid,
        primaryjoin=offer_uuid == Offer.uuid)
