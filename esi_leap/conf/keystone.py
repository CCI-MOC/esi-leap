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

import copy

from keystoneauth1 import loading
from oslo_config import cfg


opts = []
keystone_group = cfg.OptGroup('keystone', title='Keystone Options')


def register_opts(conf):
    conf.register_opts(opts, group=keystone_group)
    loading.register_session_conf_options(conf, keystone_group)
    loading.register_auth_conf_options(conf, keystone_group)
    loading.register_adapter_conf_options(conf, keystone_group)
    conf.set_default('valid_interfaces', ['internal', 'public'],
                     group=keystone_group)
    conf.set_default('service_type', 'identity', group=keystone_group)


def list_opts():
    def add_options(opts, opts_to_add):
        for new_opt in opts_to_add:
            for opt in opts:
                if opt.name == new_opt.name:
                    break
            else:
                opts.append(new_opt)

    opts_copy = copy.deepcopy(opts)
    opts_copy.insert(0, loading.get_auth_common_conf_options()[0])

    plugins = ['password', 'v2password', 'v3password']
    for name in plugins:
        plugin = loading.get_plugin_loader(name)
        add_options(opts_copy, loading.get_auth_plugin_conf_options(plugin))
    add_options(opts_copy, loading.get_session_conf_options())

    adapter_opts = loading.get_adapter_conf_options(
        include_deprecated=False)
    # adding defaults for valid interfaces
    cfg.set_defaults(adapter_opts, service_type='identity',
                     valid_interfaces=['internal', 'public'])
    add_options(opts_copy, adapter_opts)
    opts_copy.sort(key=lambda x: x.name)
    return opts_copy
