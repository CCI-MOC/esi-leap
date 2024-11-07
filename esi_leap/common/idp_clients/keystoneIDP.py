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

from keystoneauth1 import loading as ks_loading
from keystoneclient import client as keystone_client

from esi_leap.common.idp_clients import baseIDP
import esi_leap.conf

CONF = esi_leap.conf.CONF


class KeystoneIDP(baseIDP.BaseIDP):
    def __init__(self) -> None:
        auth_plugin = ks_loading.load_auth_from_conf_options(CONF, "keystone")
        sess = ks_loading.load_session_from_conf_options(
            CONF, "keystone", auth=auth_plugin
        )
        self.cli = keystone_client.Client(session=sess)

    def get_projects(self, project_id):
        return self.cli.projects.get(project_id)

    def list_projects(self, **kwargs):
        return self.cli.projects.list(**kwargs)
