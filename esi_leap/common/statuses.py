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

ACTIVE = 'active'
AVAILABLE = 'available'
CREATED = 'created'
DELETED = 'deleted'
ERROR = 'error'
EXPIRED = 'expired'
WAIT_CANCEL = 'wait cancel'
WAIT_EXPIRE = 'wait expire'
WAIT_FULFILL = 'wait fulfill'

OFFER_CAN_DELETE = [AVAILABLE, ERROR]
LEASE_CAN_DELETE = [ACTIVE, CREATED, ERROR, WAIT_FULFILL]
