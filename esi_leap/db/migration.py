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
from oslo_log import log as logging
from stevedore import driver

_IMPL = None

LOG = logging.getLogger(__name__)


def get_backend():
    global _IMPL
    if not _IMPL:
        cfg.CONF.import_opt('backend', 'oslo_db.options', group='database')
        _IMPL = driver.DriverManager('esi_leap.database.migration_backend',
                                     cfg.CONF.database.backend).driver
    return _IMPL


def version():
    return get_backend().version()


def create_schema():
    return get_backend().create_schema()


def upgrade(revision=None):
    return get_backend().upgrade(revision)


def downgrade(revision=None):
    return get_backend().downgrade(revision)


def stamp(revision):
    return get_backend().stamp(revision)


def revision(message, autogenerate):
    return get_backend().revision(message, autogenerate)
