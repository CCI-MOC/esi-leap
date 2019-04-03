from oslo_config import cfg

from esi_leap.conf import ironic

CONF = cfg.CONF

ironic.register_opts(CONF)
