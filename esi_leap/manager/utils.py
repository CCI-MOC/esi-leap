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

import oslo_messaging as messaging

import esi_leap.conf


CONF = esi_leap.conf.CONF
NAMESPACE = "manager.api"
RPC_API_VERSION = "1.0"
TOPIC = "esi_leap.manager"


def get_target():
    return messaging.Target(
        topic=TOPIC, server=CONF.host, version=RPC_API_VERSION, namespace=NAMESPACE
    )
