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


from esi_leap.conf import api
from esi_leap.conf import dummy_node
from esi_leap.conf import ironic
from esi_leap.conf import keystone
from esi_leap.conf import netconf
from esi_leap.conf import notification
from esi_leap.conf import pecan
from oslo_config import cfg

CONF = cfg.CONF


CONF.register_group(cfg.OptGroup(name='database'))
api.register_opts(CONF)
dummy_node.register_opts(CONF)
ironic.register_opts(CONF)
keystone.register_opts(CONF)
netconf.register_opts(CONF)
notification.register_opts(CONF)
pecan.register_opts(CONF)
