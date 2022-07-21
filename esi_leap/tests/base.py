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

import fixtures

from oslo_concurrency import lockutils
from oslo_config import fixture as config
from oslo_context import context as ctx
from oslo_db.sqlalchemy import enginefacade
from oslotest import base

import esi_leap.conf
from esi_leap.db import api as db_api
from esi_leap.db.sqlalchemy import models


_DB_CACHE = None
CONF = esi_leap.conf.CONF


class Database(fixtures.Fixture):

    def __init__(self, engine, sql_connection, sqlite_clean_db):
        self.sql_connection = sql_connection
        self.sqlite_clean_db = sqlite_clean_db

        self.engine = engine
        self.engine.dispose()

        models.Base.metadata.create_all(self.engine)

        conn = self.engine.connect()
        self._DB = ''.join(line for line in conn.connection.iterdump())
        self.engine.dispose()

    def setUp(self):
        super(Database, self).setUp()

        if self.sql_connection == 'sqlite://':
            conn = self.engine.connect()
            conn.connection.executescript(self._DB)
            self.addCleanup(self.engine.dispose)


class TestCase(base.BaseTestCase):

    def setUp(self):
        self.config = self.useFixture(config.Config(lockutils.CONF)).config
        super(TestCase, self).setUp()

        if not hasattr(self, 'context'):
            self.context = ctx.RequestContext(
                auth_token=None,
                project_id='12345',
                is_admin=True,
                overwrite=False)


class DBTestCase(TestCase):

    def setUp(self):
        super(DBTestCase, self).setUp()
        CONF.set_override('connection', 'sqlite://', group='database')

        self.db_api = db_api.get_instance()

        global _DB_CACHE
        if not _DB_CACHE:
            engine = enginefacade.get_legacy_facade().get_engine()
            _DB_CACHE = Database(engine,
                                 sql_connection=CONF.database.connection,
                                 sqlite_clean_db='clean.sqlite')
        self.useFixture(_DB_CACHE)
