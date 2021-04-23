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

import esi_leap.conf


CONF = esi_leap.conf.CONF
_cached_keystone_client = None


def get_keystone_client():
    global _cached_keystone_client
    if _cached_keystone_client is not None:
        return _cached_keystone_client

    auth_plugin = ks_loading.load_auth_from_conf_options(CONF, 'keystone')
    sess = ks_loading.load_session_from_conf_options(CONF, 'keystone',
                                                     auth=auth_plugin)
    cli = keystone_client.Client(session=sess)
    _cached_keystone_client = cli

    return cli


def get_parent_project_id_tree(project_id):
    project = get_keystone_client().projects.get(project_id)
    project_ids = [project.id]
    while project.parent_id is not None:
        project = get_keystone_client().projects.get(project.parent_id)
        project_ids.append(project.id)
    return project_ids
