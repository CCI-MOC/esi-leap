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

"""
Websocket proxy adapted from similar code in Nova
"""

import socket
import threading
import traceback
from urllib import parse as urlparse
import websockify

from oslo_log import log as logging
from oslo_utils import importutils
from oslo_utils import timeutils

from esi_leap.common import exception
from esi_leap.common import ironic
import esi_leap.conf
from esi_leap.objects import console_auth_token


CONF = esi_leap.conf.CONF
LOG = logging.getLogger(__name__)


# Location of WebSockifyServer class in websockify v0.9.0
websockifyserver = importutils.try_import("websockify.websockifyserver")


class ProxyRequestHandler(websockify.ProxyRequestHandler):
    def __init__(self, *args, **kwargs):
        websockify.ProxyRequestHandler.__init__(self, *args, **kwargs)

    def verify_origin_proto(self, connect_info, origin_proto):
        if "access_url_base" not in connect_info:
            detail = "No access_url_base in connect_info."
            raise Exception(detail)

        expected_protos = [urlparse.urlparse(connect_info.access_url_base).scheme]
        # NOTE: For serial consoles the expected protocol could be ws or
        # wss which correspond to http and https respectively in terms of
        # security.
        if "ws" in expected_protos:
            expected_protos.append("http")
        if "wss" in expected_protos:
            expected_protos.append("https")

        return origin_proto in expected_protos

    def _get_connect_info(self, token):
        """Validate the token and get the connect info."""
        connect_info = console_auth_token.ConsoleAuthToken.validate(token)
        if CONF.serialconsoleproxy.timeout > 0:
            connect_info.expires = (
                timeutils.utcnow_ts() + CONF.serialconsoleproxy.timeout
            )

        # get host and port
        console_info = ironic.get_ironic_client().node.get_console(
            connect_info.node_uuid
        )
        console_type = console_info["console_info"]["type"]
        if console_type != "socat":
            raise exception.UnsupportedConsoleType(
                console_type=console_type,
            )
        url = urlparse.urlparse(console_info["console_info"]["url"])
        connect_info.host = url.hostname
        connect_info.port = url.port

        return connect_info

    def _close_connection(self, tsock, host, port):
        """takes target socket and close the connection."""
        try:
            tsock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        finally:
            if tsock.fileno() != -1:
                tsock.close()
                LOG.debug(
                    "%(host)s:%(port)s: "
                    "Websocket client or target closed" % {"host": host, "port": port}
                )

    def new_websocket_client(self):
        """Called after a new WebSocket connection has been established."""
        # Reopen the eventlet hub to make sure we don't share an epoll
        # fd with parent and/or siblings, which would be bad
        from eventlet import hubs

        hubs.use_hub()

        token = (
            urlparse.parse_qs(urlparse.urlparse(self.path).query)
            .get("token", [""])
            .pop()
        )

        try:
            connect_info = self._get_connect_info(token)
        except Exception:
            LOG.debug(traceback.format_exc())
            raise

        host = connect_info.host
        port = connect_info.port

        # Connect to the target
        LOG.debug("Connecting to: %(host)s:%(port)s" % {"host": host, "port": port})
        tsock = self.socket(host, port, connect=True)

        # Start proxying
        try:
            if CONF.serialconsoleproxy.timeout > 0:
                conn_timeout = connect_info.expires - timeutils.utcnow_ts()
                LOG.debug("%s seconds to terminate connection." % conn_timeout)
                threading.Timer(
                    conn_timeout, self._close_connection, [tsock, host, port]
                ).start()
            self.do_proxy(tsock)
        except Exception:
            LOG.debug(traceback.format_exc())
            raise
        finally:
            self._close_connection(tsock, host, port)

    def socket(self, *args, **kwargs):
        return websockifyserver.WebSockifyServer.socket(*args, **kwargs)


class WebSocketProxy(websockify.WebSocketProxy):
    def __init__(self, *args, **kwargs):
        super(WebSocketProxy, self).__init__(*args, **kwargs)

    @staticmethod
    def get_logger():
        return LOG
