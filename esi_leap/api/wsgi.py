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

from oslo_log import log as logging

from esi_leap.api.app import WSGIApplication
from esi_leap.common import i18n
from esi_leap.common import service
import esi_leap.conf


CONF = esi_leap.conf.CONF
LOG = logging.getLogger(__name__)


def initialize_wsgi_app(argv=sys.argv):
    i18n.install('esi_leap')

    service.prepare_service(argv)

    LOG.debug('Configuration:')
    CONF.log_opt_values(LOG, logging.DEBUG)

    return WSGIApplication()
