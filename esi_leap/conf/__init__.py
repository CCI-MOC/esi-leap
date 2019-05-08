from oslo_config import cfg

from esi_leap.conf import api
from esi_leap.conf import ironic
from esi_leap.conf import netconf
from esi_leap.conf import pecan


CONF = cfg.CONF


CONF.register_group(cfg.OptGroup(name='database'))
api.register_opts(CONF)
ironic.register_opts(CONF)
netconf.register_opts(CONF)
pecan.register_opts(CONF)
