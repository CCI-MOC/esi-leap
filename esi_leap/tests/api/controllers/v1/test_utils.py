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

from oslo_context import context as ctx

from esi_leap.api.controllers.v1 import utils

admin_context = ctx.RequestContext()
admin_context.roles = ['admin']
admin_context = admin_context.to_policy_values()

random_context = ctx.RequestContext()
random_context.roles = ['randomrole']
random_context = random_context.to_policy_values()


def test_verify_admin():
    assert utils.verify_admin(admin_context) is True
    assert utils.verify_admin(random_context) is False
