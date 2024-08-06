# All Rights Reserved.
#
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

from esi_leap.common import service as esi_leap_service
from esi_leap.console import websocketproxy
import esi_leap.conf


CONF = esi_leap.conf.CONF


def main():
    esi_leap_service.prepare_service(sys.argv)
    websocketproxy.WebSocketProxy(
        listen_host=CONF.serialconsoleproxy.host_address,
        listen_port=CONF.serialconsoleproxy.port,
        file_only=True,
        RequestHandlerClass=websocketproxy.ProxyRequestHandler,
    ).start_server()
