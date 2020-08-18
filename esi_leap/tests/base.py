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
from oslotest import base

import esi_leap.conf
from esi_leap.db import api as db_api
from esi_leap.db.sqlalchemy import api as sql_api


_DB_CACHE = None
CONF = esi_leap.conf.CONF


class Database(fixtures.Fixture):

    def setUp(self):
        super(Database, self).setUp()
        CONF.set_override('connection', 'sqlite://',
                          group='database')

        sql_api.reset_facade()
        sql_api.setup_db()
        self.addCleanup(sql_api.drop_db)


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
        self.db_api = db_api.get_instance()

        global _DB_CACHE
        if not _DB_CACHE:
            _DB_CACHE = Database()
        self.useFixture(_DB_CACHE)
