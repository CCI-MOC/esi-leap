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

from oslo_service import service

from esi_leap.common import service as esi_leap_service
import esi_leap.conf
from esi_leap.manager import service as manager_service


CONF = esi_leap.conf.CONF


def main():
    esi_leap_service.prepare_service(sys.argv)
    service.launch(
        CONF,
        manager_service.ManagerService(),
        restart_method='mutate'
    ).wait()
