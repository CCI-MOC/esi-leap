from oslo_config import cfg

from esi_leap.conf import ironic
from esi_leap.conf import netconf

CONF = cfg.CONF

CONF.register_group(cfg.OptGroup(name='database'))
ironic.register_opts(CONF)
netconf.register_opts(CONF)
