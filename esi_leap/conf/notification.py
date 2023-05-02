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

from esi_leap.common.i18n import _
from oslo_config import cfg

# borrowed from Ironic
opts = [
    cfg.StrOpt('notification_level',
               choices=[('debug', _('"debug" level')),
                        ('info', _('"info" level')),
                        ('warning', _('"warning" level')),
                        ('error', _('"error" level')),
                        ('critical', _('"critical" level'))],
               help=_('Specifies the minimum level for which to send '
                      'notifications. If not set, no notifications will '
                      'be sent.')),
    cfg.ListOpt(
        'versioned_notifications_topics',
        default=['esi_leap_versioned_notifications'],
        help=_('Specifies the topics for '
               'the versioned notifications issued by esi-leap.')),
]


notification_group = cfg.OptGroup('notification', title='Notification Options')


def register_opts(conf):
    conf.register_opts(opts, group=notification_group)
    conf.set_default('notification_level', 'info', group=notification_group)
