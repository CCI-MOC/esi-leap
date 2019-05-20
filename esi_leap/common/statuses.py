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

# lease request statuses
PENDING = 'pending'      # requested but not fulfilled
FULFILLED = 'fulfilled'  # fulfilled and lease timer is running
DEGRADED = 'degraded'    # fulfilled but resource(s) have been reclaimed
EXPIRED = 'expired'      # fulfilled and has reached its expiration date
CANCELLED = 'cancelled'  # ended prematurely
DELETED = 'deleted'      # deleted
