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
    def get_uuid(self):
        """Return resource's uuid"""

    @abc.abstractmethod
    def get_name(self, resource_list):
        """Return resource's name, if any"""

    @abc.abstractmethod
    def get_resource_class(self, resource_list):
        """Return resource's associated class, if any"""

    @abc.abstractmethod
    def get_config(self):
        """Return resource's associated config, if any"""

    @abc.abstractmethod
    def get_owner_project_id(self):
        """Return the project id of the resource's owner"""

    @abc.abstractmethod
    def get_lease_uuid(self):
        """Return the uuid of the associated lease, if any"""

    @abc.abstractmethod
    def get_lessee_project_id(self):
        """Return the project id of the associated lessee, if any"""

    @abc.abstractmethod
    def get_node_provision_state(self, resource_list):
        """Return resource's provision state, if any"""

    @abc.abstractmethod
    def get_node_power_state(self, resource_list):
        """Return resource's power state, if any"""

    @abc.abstractmethod
    def set_lease(self, lease):
        """Associates a lease with the resource"""

    @abc.abstractmethod
    def remove_lease(self, lease):
        """Disassociates a lease from the resource"""

    def verify_availability(self, start_time, end_time):
        self.dbapi.resource_verify_availability(
            self.resource_type,
            self.get_uuid(),
            start_time,
            end_time,
        )
