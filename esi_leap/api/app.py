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

from keystonemiddleware import auth_token
from oslo_context import context
import pecan
from pecan import hooks

import esi_leap.conf


CONF = esi_leap.conf.CONF


class ContextHook(hooks.PecanHook):
    def before(self, state):
        ctx = context.RequestContext.from_environ(state.request.environ)
        state.request.context = ctx

    def after(self, state):
        state.request.context = None


def get_pecan_config():
    cfg_dict = {
        'app': {
            'root': CONF.pecan.root,
            'modules': CONF.pecan.modules,
            'debug': CONF.pecan.debug,
            'auth_enable': CONF.pecan.auth_enable
        }
    }

    return pecan.configuration.conf_from_dict(cfg_dict)


def setup_app(config=None):
    if not config:
        config = get_pecan_config()

    pecan.configuration.set_config(dict(config), overwrite=True)

    app = pecan.make_app(
        config.app.root,
        hooks=lambda: [ContextHook()],
        debug=CONF.pecan.debug,
        static_root=config.app.static_root if CONF.pecan.debug else None,
        force_canonical=getattr(config.app, 'force_canonical', True),
    )

    if CONF.pecan.auth_enable:
        app = auth_token.AuthProtocol(app, dict(CONF.keystone_authtoken))

    return app


class WSGIApplication(object):
    def __init__(self):
        pecan_cfg = get_pecan_config()
        self.app = setup_app(pecan_cfg)

    def __call__(self, environ, start_response):
        return self.app(environ, start_response)
