
import pecan

from keystonemiddleware import auth_token
from flocx_provider.api import config as api_config
from flocx_provider.api import hooks


def get_pecan_config():
    filename = api_config.__file__.replace('.pyc', '.py')
    return pecan.configuration.conf_from_file(filename)



def setup_app():
    config = get_pecan_config()

    app_hooks = [hooks.DBHook()]
    app_conf = dict(config.app)
    app = pecan.make_app(
        app_conf.pop('root'),
        logging=getattr(config, 'logging', {}),
        hooks=app_hooks,
        **app_conf
    )
    keystone_config = {
    'auth_plugin':'password',
    # 'auth_type':'password',
    # 'service_token_roles_required': True,
    #'www_authenticate_uri': 'http://localhost:5000',
    'auth_url': 'http://localhost:5000',
    # 'auth_port':
    # 'identity_uri': 'http://localhost:5000/v3',
    'username':'admin',
    'password':'qwerty123',
    'project_name':'admin',
    'project_domain_name':'Default',
    'user_domain_name': 'Default',
    #'delay_auth_decision':True

    # 'identity_uri':'http://127.0.0.1:5000', user 
    # 'admin_user': 'admin',
    # 'admin_password':'ADMIN_PASS'

    }

    return auth_token.AuthProtocol(app, keystone_config)

    #return app

