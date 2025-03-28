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

import datetime

from oslo_concurrency import lockutils

_prefix = "esileap"
lock = lockutils.lock_with_prefix(_prefix)


def get_resource_lock_name(resource_type, resource_uuid):
    return resource_type + "-" + resource_uuid


def datetime_aware(dt):
    if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
        return dt
    return dt.replace(tzinfo=datetime.timezone.utc)
