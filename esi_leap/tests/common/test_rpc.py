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

from esi_leap.common import rpc
from esi_leap.tests import base

import mock

from oslo_config import cfg
from oslo_context import context as ctx
import oslo_messaging as messaging

CONF = cfg.CONF


# TestUtils borrowed from Ironic
class TestUtils(base.TestCase):

    @mock.patch.object(messaging, 'Notifier', autospec=True)
    @mock.patch.object(messaging, 'JsonPayloadSerializer', autospec=True)
    @mock.patch.object(messaging, 'get_notification_transport', autospec=True)
    def test_init_globals_notifications_disabled(self,
                                                 mock_get_notification,
                                                 mock_json_serializer,
                                                 mock_notifier):
        self._test_init_globals(False,
                                mock_get_notification, mock_json_serializer,
                                mock_notifier)

    @mock.patch.object(messaging, 'Notifier', autospec=True)
    @mock.patch.object(messaging, 'JsonPayloadSerializer', autospec=True)
    @mock.patch.object(messaging, 'get_notification_transport', autospec=True)
    def test_init_globals_notifications_enabled(self,
                                                mock_get_notification,
                                                mock_json_serializer,
                                                mock_notifier):
        self.config(notification_level='debug', group='notification')
        self._test_init_globals(True,
                                mock_get_notification, mock_json_serializer,
                                mock_notifier)

    def _test_init_globals(
        self, notifications_enabled,
        mock_get_notification, mock_json_serializer,
        mock_notifier,
        versioned_notifications_topics=(
            ['esi_leap_versioned_notifications'])):

        rpc.NOTIFICATION_TRANSPORT = None
        rpc.VERSIONED_NOTIFIER = None
        mock_request_serializer = mock.Mock()
        mock_request_serializer.return_value = mock.Mock()
        rpc.RequestContextSerializer = mock_request_serializer

        mock_notifier.return_value = mock.Mock()

        rpc.init(CONF)

        self.assertEqual(mock_get_notification.return_value,
                         rpc.NOTIFICATION_TRANSPORT)
        self.assertTrue(mock_json_serializer.called)

        if not notifications_enabled:
            mock_notifier.assert_any_call(
                rpc.NOTIFICATION_TRANSPORT,
                serializer=mock_request_serializer.return_value,
                driver='noop')
        else:
            mock_notifier.assert_any_call(
                rpc.NOTIFICATION_TRANSPORT,
                serializer=mock_request_serializer.return_value,
                topics=versioned_notifications_topics)

        self.assertEqual(mock_notifier.return_value, rpc.VERSIONED_NOTIFIER)

    def test_get_versioned_notifier(self):
        rpc.VERSIONED_NOTIFIER = mock.Mock(autospec=True)
        rpc.get_versioned_notifier(publisher_id='a_great_publisher')
        rpc.VERSIONED_NOTIFIER.prepare.assert_called_once_with(
            publisher_id='a_great_publisher')

    def test_get_versioned_notifier_no_publisher_id(self):
        rpc.VERSIONED_NOTIFIER = mock.Mock()
        self.assertRaises(AssertionError,
                          rpc.get_versioned_notifier, publisher_id=None)

    def test_get_versioned_notifier_no_notifier(self):
        rpc.VERSIONED_NOTIFIER = None
        self.assertRaises(
            AssertionError,
            rpc.get_versioned_notifier, publisher_id='a_great_publisher')


class TestRequestContextSerializer(base.TestCase):

    def setUp(self):
        super(TestRequestContextSerializer, self).setUp()

        self.mock_serializer = mock.MagicMock()
        self.serializer = rpc.RequestContextSerializer(self.mock_serializer)
        self.context = ctx.RequestContext()
        self.entity = {'foo': 'bar'}

    def test_serialize_entity(self):
        self.serializer.serialize_entity(self.context, self.entity)
        self.mock_serializer.serialize_entity.assert_called_with(
            self.context, self.entity)

    def test_serialize_entity_empty_base(self):
        # NOTE(viktors): Return False for check `if self.serializer._base:`
        bool_args = {'__bool__': lambda *args: False,
                     '__nonzero__': lambda *args: False}
        self.mock_serializer.configure_mock(**bool_args)

        entity = self.serializer.serialize_entity(self.context, self.entity)
        self.assertFalse(self.mock_serializer.serialize_entity.called)
        # If self.serializer._base is empty, return entity directly
        self.assertEqual(self.entity, entity)

    def test_deserialize_entity(self):
        self.serializer.deserialize_entity(self.context, self.entity)
        self.mock_serializer.deserialize_entity.assert_called_with(
            self.context, self.entity)

    def test_deserialize_entity_empty_base(self):
        # NOTE(viktors): Return False for check `if self.serializer._base:`
        bool_args = {'__bool__': lambda *args: False,
                     '__nonzero__': lambda *args: False}
        self.mock_serializer.configure_mock(**bool_args)

        entity = self.serializer.deserialize_entity(self.context, self.entity)
        self.assertFalse(self.mock_serializer.serialize_entity.called)
        self.assertEqual(self.entity, entity)

    def test_serialize_context(self):
        serialize_values = self.serializer.serialize_context(self.context)

        self.assertEqual(self.context.to_dict(), serialize_values)

    def test_deserialize_context(self):
        serialize_values = self.context.to_dict()
        new_context = self.serializer.deserialize_context(serialize_values)
        self.assertEqual(serialize_values, new_context.to_dict())
        self.assertIsInstance(new_context, ctx.RequestContext)
