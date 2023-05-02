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

import esi_leap.conf

_opts = [
    ('DEFAULT', esi_leap.conf.netconf.opts),
    ('api', esi_leap.conf.api.opts),
    ('dummy_node', esi_leap.conf.dummy_node.opts),
    ('ironic', esi_leap.conf.ironic.list_opts()),
    ('keystone', esi_leap.conf.keystone.list_opts()),
    ('pecan', esi_leap.conf.pecan.opts),
    ('notification', esi_leap.conf.notification.opts),
]


def list_opts():
    return _opts
