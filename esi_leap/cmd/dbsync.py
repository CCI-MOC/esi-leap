from __future__ import print_function

import sys

from oslo_config import cfg

import esi_leap.conf
from esi_leap.common.i18n import _
from esi_leap.common import service
from esi_leap.db import migration


CONF = esi_leap.conf.CONF


class DBCommand(object):

    def create_schema(self):
        migration.create_schema()


def add_command_parsers(subparsers):
    command_object = DBCommand()

    parser = subparsers.add_parser(
        'create_schema',
        help=_("Create the database schema."))
    parser.set_defaults(func=command_object.create_schema)


def main():
    command_opt = cfg.SubCommandOpt('command',
                                    title='Command',
                                    help=_('Available commands'),
                                    handler=add_command_parsers)

    CONF.register_cli_opt(command_opt)

    service.prepare_service(sys.argv)
    CONF.command.func()
