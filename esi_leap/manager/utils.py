import oslo_messaging as messaging

import esi_leap.conf


CONF = esi_leap.conf.CONF
NAMESPACE = 'manager.api'
RPC_API_VERSION = '1.0'
TOPIC = 'esi_leap.manager'


def get_target():
    return messaging.Target(topic=TOPIC,
                            server=CONF.host,
                            version=RPC_API_VERSION,
                            namespace=NAMESPACE)
