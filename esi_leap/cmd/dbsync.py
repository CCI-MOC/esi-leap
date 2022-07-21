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

from __future__ import print_function

import sys

from oslo_config import cfg

from esi_leap.common.i18n import _
from esi_leap.common import service
import esi_leap.conf
from esi_leap.db import migration


CONF = esi_leap.conf.CONF


class DBCommand(object):

    def create_schema(self):
        migration.create_schema()

    def upgrade(self):
        migration.upgrade(CONF.command.revision)

    def downgrade(self):
        migration.downgrade(CONF.command.revision)

    def stamp(self):
        migration.stamp(CONF.command.revision)

    def revision(self):
        migration.revision(CONF.command.message, CONF.command.autogenerate)

    def version(self):
        print(migration.version())


def add_command_parsers(subparsers):
    command_object = DBCommand()

    parser = subparsers.add_parser(
        'create_schema',
        help=_('Create the database schema.'))
    parser.set_defaults(func=command_object.create_schema)

    parser = subparsers.add_parser(
        'upgrade',
        help=_('Upgrade the database.'))
    parser.set_defaults(func=command_object.upgrade)
    parser.add_argument('--revision', nargs='?')

    parser = subparsers.add_parser(
        'downgrade',
        help=_('Downgrade the database.'))
    parser.set_defaults(func=command_object.downgrade)
    parser.add_argument('--revision', nargs='?')

    parser = subparsers.add_parser(
        'stamp',
        help=_('Stamp the database with provided revision.'))
    parser.set_defaults(func=command_object.stamp)
    parser.add_argument('--revision', nargs='?')

    parser = subparsers.add_parser(
        'revision',
        help=_('Creates template for migration'))
    parser.set_defaults(func=command_object.revision)
    parser.add_argument('-m', '--message')
    parser.add_argument('--autogenerate', action='store_true')

    parser = subparsers.add_parser(
        'version',
        help=_('Print the current version information and exit.'))
    parser.set_defaults(func=command_object.version)


def main():
    command_opt = cfg.SubCommandOpt('command',
                                    title='Command',
                                    help=_('Available commands'),
                                    handler=add_command_parsers)

    CONF.register_cli_opt(command_opt)

    service.prepare_service(sys.argv)
    CONF.command.func()
