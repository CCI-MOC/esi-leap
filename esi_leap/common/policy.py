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

import itertools

from oslo_policy import policy

import esi_leap.conf

CONF = esi_leap.conf.CONF
_ENFORCER = None

default_policies = [
    policy.RuleDefault('is_admin',
                       'role:admin or role:esi_leap_admin',
                       description='Full read/write API access'),
    policy.RuleDefault('is_owner',
                       'role:owner or role:esi_leap_owner',
                       description='Owner API access'),
    policy.RuleDefault('is_lessee',
                       'role:lessee or role:esi_leap_lessee',
                       description='Lessee API access'),
]

contract_policies = [
    policy.DocumentedRuleDefault(
        'esi_leap:contract:contract_admin',
        'rule:is_admin',
        'Complete permissions over contracts',
        [{'path': '/contracts', 'method': 'POST'},
         {'path': '/contracts', 'method': 'GET'},
         {'path': '/contracts/{contract_ident}', 'method': 'GET'},
         {'path': '/contracts/{contract_ident}', 'method': 'DELETE'}]),
    policy.DocumentedRuleDefault(
        'esi_leap:contract:create',
        'rule:is_admin or rule:is_lessee',
        'Create contract',
        [{'path': '/contracts', 'method': 'POST'}]),
    policy.DocumentedRuleDefault(
        'esi_leap:contract:get',
        'rule:is_admin or rule:is_lessee or rule:is_owner',
        'Retrieve all contracts owned by project_id',
        [{'path': '/contracts', 'method': 'GET'},
         {'path': '/contracts/{contract_ident}', 'method': 'GET'}]),
    policy.DocumentedRuleDefault(
        'esi_leap:contract:delete',
        'rule:is_admin or rule:is_owner or rule:is_lessee',
        'Delete contract',
        [{'path': '/contracts/{contract_ident}', 'method': 'DELETE'}]),
]

offer_policies = [
    policy.DocumentedRuleDefault(
        'esi_leap:offer:offer_admin',
        'rule:is_admin',
        'Complete permissions over offers',
        [{'path': '/offers', 'method': 'POST'},
         {'path': '/offers', 'method': 'GET'},
         {'path': '/offers/{offer_ident}', 'method': 'GET'},
         {'path': '/offers/{offer_ident}', 'method': 'DELETE'}]),
    policy.DocumentedRuleDefault(
        'esi_leap:offer:create',
        'rule:is_admin or rule:is_owner',
        'Create offer',
        [{'path': '/offers', 'method': 'POST'}]),
    policy.DocumentedRuleDefault(
        'esi_leap:offer:get',
        'rule:is_admin or rule:is_owner or rule:is_lessee',
        'Retrieve offer',
        [{'path': '/offers', 'method': 'GET'},
         {'path': '/offers/{offer_ident}', 'method': 'GET'}]),
    policy.DocumentedRuleDefault(
        'esi_leap:offer:delete',
        'rule:is_admin or rule:is_owner',
        'Delete offer',
        [{'path': '/offers/{offer_ident}', 'method': 'DELETE'}]),
]


def list_rules():
    policies = itertools.chain(
        default_policies,
        contract_policies,
        offer_policies,
    )
    return policies


def get_enforcer():
    CONF([], project='esi-leap')
    global _ENFORCER
    if not _ENFORCER:
        _ENFORCER = policy.Enforcer(CONF)
        _ENFORCER.register_defaults(list_rules())
    return _ENFORCER


def authorize(rule, target, creds, *args, **kwargs):
    if not CONF.pecan.auth_enable:
        return True

    return get_enforcer().authorize(
        rule, target, creds, do_raise=True, *args, **kwargs)
