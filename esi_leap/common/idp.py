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

from oslo_utils import uuidutils

from esi_leap.common import exception
import esi_leap.conf
from esi_leap.common.idp_clients import baseIDP
from esi_leap.common.idp_clients import keystoneIDP  # noqa: F401
from esi_leap.common.idp_clients import dummyIDP  # noqa: F401


CONF = esi_leap.conf.CONF
IDP_TYPE_MAP = {idp.idp_type: idp for idp in baseIDP.BaseIDP.__subclasses__()}
_cached_idp_client = None
_cached_project_list = None


def get_idp_client():
    global _cached_idp_client
    if _cached_idp_client is not None:
        return _cached_idp_client

    # Get Client config option
    idp_type = CONF.esi.idp_type
    cli = IDP_TYPE_MAP[idp_type]()
    _cached_idp_client = cli

    return cli


def get_parent_project_id_tree(project_id):
    idp = get_idp_client()
    project = idp.get_projects(project_id)
    project_ids = [project.id]
    while project.parent_id is not None:
        project = idp.get_projects(project.parent_id)
        project_ids.append(project.id)
    return project_ids


def get_project_uuid_from_ident(project_ident):
    if uuidutils.is_uuid_like(project_ident):
        return project_ident
    else:
        projects = get_idp_client().list_projects(name=project_ident)
        if len(projects) > 0:
            # projects have unique names
            return projects[0].id
        raise exception.ProjectNoSuchName(name=project_ident)


def get_project_list():
    return get_idp_client().list_projects()


def get_project_name(project_id, project_list=None):
    if project_id:
        if project_list is None:
            project = get_idp_client().get_projects(project_id)
        else:
            project = next(
                (p for p in project_list if getattr(p, "id") == project_id), None
            )
        return project.name if project else ""
    else:
        return ""
