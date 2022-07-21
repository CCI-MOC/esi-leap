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
from oslo_utils import uuidutils

from esi_leap.common import exception
import esi_leap.conf


CONF = esi_leap.conf.CONF
_cached_keystone_client = None
_cached_project_list = None


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
    ks_client = get_keystone_client()
    project = ks_client.projects.get(project_id)
    project_ids = [project.id]
    while project.parent_id is not None:
        project = ks_client.projects.get(project.parent_id)
        project_ids.append(project.id)
    return project_ids


def get_project_uuid_from_ident(project_ident):
    if uuidutils.is_uuid_like(project_ident):
        return project_ident
    else:
        projects = get_keystone_client().projects.list(name=project_ident)
        if len(projects) > 0:
            # projects have unique names
            return projects[0].id
        raise exception.ProjectNoSuchName(name=project_ident)


def get_project_list():
    return get_keystone_client().projects.list()


def get_project_name(project_id, project_list=None):
    if project_id:
        if project_list is None:
            project = get_keystone_client().projects.get(project_id)
        else:
            project = next((p for p in project_list
                            if getattr(p, 'id') == project_id),
                           None)
        return project.name if project else ''
    else:
        return ''
