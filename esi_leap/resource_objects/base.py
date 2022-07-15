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

import abc

from esi_leap.db import api as dbapi


class ResourceObjectInterface(object, metaclass=abc.ABCMeta):
    dbapi = dbapi.get_instance()

    resource_type = 'base'

    @abc.abstractmethod
    def get_resource_uuid(self):
        """Returns resource's uuid"""

    @abc.abstractmethod
    def get_resource_name(self, resource_list):
        """Returns resource's name"""

    @abc.abstractmethod
    def get_lease_uuid(self):
        """Returns resource's associated lease, if any"""

    @abc.abstractmethod
    def get_project_id(self):
        """Returns resource's associated lessee, if any"""

    @abc.abstractmethod
    def get_node_config(self):
        """Returns resource's associated config, if any"""

    @abc.abstractmethod
    def get_resource_class(self):
        """Returns resource's associated class, if any"""

    @abc.abstractmethod
    def set_lease(self, lease):
        """Set the lease on the node"""

    @abc.abstractmethod
    def expire_lease(self, lease):
        """Expire the lease on the node"""

    @abc.abstractmethod
    def resource_admin_project_id(self):
        """Return project_id of resource admin"""

    def verify_availability(self, start_time, end_time):
        self.dbapi.resource_verify_availability(
            self.resource_type,
            self.get_resource_uuid(),
            start_time,
            end_time,
        )
