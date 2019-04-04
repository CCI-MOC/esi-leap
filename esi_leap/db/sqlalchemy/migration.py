import os

from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import enginefacade

from esi_leap.db.sqlalchemy import models


def create_schema(config=None, engine=None):
    """Create database schema from models description.

    Can be used for initial installation instead of upgrade('head').
    """
    if engine is None:
        engine = enginefacade.writer.get_engine()
    models.Base.metadata.create_all(engine)

