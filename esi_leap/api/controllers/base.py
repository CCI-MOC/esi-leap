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

import wsme
from wsme import types as wtypes


class ESILEAPBase(wtypes.Base):

    def to_dict(self):
        esi_leap_dict = {}
        if self.fields:
            for key in self.fields:
                val = getattr(self, key, wsme.Unset)
                if val != wsme.Unset:
                    esi_leap_dict[key] = val
        return esi_leap_dict
