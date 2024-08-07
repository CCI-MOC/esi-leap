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

import mock

from esi_leap.common import exception
from esi_leap.objects import base
from esi_leap.objects import fields
from esi_leap.objects import notification
from esi_leap.tests import base as test_base

from oslo_serialization import jsonutils
from oslo_versionedobjects import base as versioned_objects_base


# Notification object borrowed from Ironic
class TestNotificationBase(test_base.TestCase):
    @versioned_objects_base.VersionedObjectRegistry.register
    class TestObject(base.ESILEAPObject):
        VERSION = "1.0"
        fields = {
            "fake_field_1": fields.StringField(nullable=True),
            "fake_field_2": fields.IntegerField(nullable=True),
        }

    @versioned_objects_base.VersionedObjectRegistry.register
    class TestObjectMissingField(base.ESILEAPObject):
        VERSION = "1.0"
        fields = {
            "fake_field_1": fields.StringField(nullable=True),
        }

    @versioned_objects_base.VersionedObjectRegistry.register
    class TestNotificationPayload(notification.NotificationPayloadBase):
        VERSION = "1.0"

        SCHEMA = {
            "fake_field_a": ("test_obj", "fake_field_1"),
            "fake_field_b": ("test_obj", "fake_field_2"),
        }

        fields = {
            "fake_field_a": fields.StringField(nullable=True),
            "fake_field_b": fields.IntegerField(nullable=False),
            "an_extra_field": fields.StringField(nullable=False),
            "an_optional_field": fields.IntegerField(nullable=True),
        }

    @versioned_objects_base.VersionedObjectRegistry.register
    class TestNotificationPayloadEmptySchema(notification.NotificationPayloadBase):
        VERSION = "1.0"

        fields = {"fake_field": fields.StringField()}

    @versioned_objects_base.VersionedObjectRegistry.register
    class TestNotification(notification.NotificationBase):
        VERSION = "1.0"
        fields = {"payload": fields.ObjectField("TestNotificationPayload")}

    @versioned_objects_base.VersionedObjectRegistry.register
    class TestNotificationEmptySchema(notification.NotificationBase):
        VERSION = "1.0"
        fields = {"payload": fields.ObjectField("TestNotificationPayloadEmptySchema")}

    def setUp(self):
        super(TestNotificationBase, self).setUp()
        self.fake_obj = self.TestObject(fake_field_1="fake1", fake_field_2=2)

    def _verify_notification(
        self,
        mock_notifier,
        mock_context,
        mock_event_create,
        expected_event_type,
        expected_payload,
        expected_publisher,
        notif_level,
    ):
        mock_notifier.prepare.assert_called_once_with(publisher_id=expected_publisher)
        # Handler actually sending out the notification depends on the
        # notification level
        mock_notify = getattr(mock_notifier.prepare.return_value, notif_level)
        self.assertTrue(mock_notify.called)
        self.assertEqual(mock_context, mock_notify.call_args[0][0])
        self.assertEqual(expected_event_type, mock_notify.call_args[1]["event_type"])
        actual_payload = mock_notify.call_args[1]["payload"]
        self.assertEqual(
            jsonutils.dumps(expected_payload, sort_keys=True),
            jsonutils.dumps(actual_payload, sort_keys=True),
        )
        mock_event_create.assert_called_once()

    @mock.patch("esi_leap.objects.event.Event.create")
    @mock.patch("esi_leap.common.rpc.VERSIONED_NOTIFIER")
    def test_emit_notification(self, mock_notifier, mock_event_create):
        self.config(notification_level="debug", group="notification")
        payload = self.TestNotificationPayload(
            an_extra_field="extra", an_optional_field=1
        )
        payload.populate_schema(test_obj=self.fake_obj)
        notif = self.TestNotification(
            event_type=notification.EventType(
                object="test_object",
                action="test",
                status=fields.NotificationStatus.START,
            ),
            level=fields.NotificationLevel.DEBUG,
            publisher=notification.NotificationPublisher(
                service="esi-leap-api", host="host"
            ),
            payload=payload,
        )

        mock_context = mock.Mock()
        notif.emit(mock_context)

        self._verify_notification(
            mock_notifier,
            mock_context,
            mock_event_create,
            expected_event_type="esi_leap.test_object.test.start",
            expected_payload={
                "esi_leap_object.name": "TestNotificationPayload",
                "esi_leap_object.data": {
                    "fake_field_a": "fake1",
                    "fake_field_b": 2,
                    "an_extra_field": "extra",
                    "an_optional_field": 1,
                },
                "esi_leap_object.version": "1.0",
                "esi_leap_object.namespace": "esi_leap",
            },
            expected_publisher="esi-leap-api.host",
            notif_level=fields.NotificationLevel.DEBUG,
        )

    @mock.patch("esi_leap.common.rpc.VERSIONED_NOTIFIER")
    def test_no_emit_level_too_low(self, mock_notifier):
        # Make sure notification doesn't emit when set notification
        # level < config level
        self.config(notification_level="warning", group="notification")
        payload = self.TestNotificationPayload(
            an_extra_field="extra", an_optional_field=1
        )
        payload.populate_schema(test_obj=self.fake_obj)
        notif = self.TestNotification(
            event_type=notification.EventType(
                object="test_object",
                action="test",
                status=fields.NotificationStatus.START,
            ),
            level=fields.NotificationLevel.DEBUG,
            publisher=notification.NotificationPublisher(
                service="esi-leap-api", host="host"
            ),
            payload=payload,
        )

        mock_context = mock.Mock()
        notif.emit(mock_context)

        self.assertFalse(mock_notifier.called)

    @mock.patch("esi_leap.common.rpc.VERSIONED_NOTIFIER")
    def test_no_emit_notifs_disabled(self, mock_notifier):
        # Make sure notifications aren't emitted when notification_level
        # isn't defined, indicating notifications should be disabled
        payload = self.TestNotificationPayload(
            an_extra_field="extra", an_optional_field=1
        )
        payload.populate_schema(test_obj=self.fake_obj)
        notif = self.TestNotification(
            event_type=notification.EventType(
                object="test_object",
                action="test",
                status=fields.NotificationStatus.START,
            ),
            level=fields.NotificationLevel.DEBUG,
            publisher=notification.NotificationPublisher(
                service="esi-leap-api", host="host"
            ),
            payload=payload,
        )

        mock_context = mock.Mock()
        notif.emit(mock_context)

        self.assertFalse(mock_notifier.called)

    @mock.patch("esi_leap.common.rpc.VERSIONED_NOTIFIER")
    def test_no_emit_schema_not_populated(self, mock_notifier):
        self.config(notification_level="debug", group="notification")
        payload = self.TestNotificationPayload(
            an_extra_field="extra", an_optional_field=1
        )
        notif = self.TestNotification(
            event_type=notification.EventType(
                object="test_object",
                action="test",
                status=fields.NotificationStatus.START,
            ),
            level=fields.NotificationLevel.DEBUG,
            publisher=notification.NotificationPublisher(
                service="esi-leap-api", host="host"
            ),
            payload=payload,
        )

        mock_context = mock.Mock()
        self.assertRaises(exception.NotificationPayloadError, notif.emit, mock_context)
        self.assertFalse(mock_notifier.called)

    @mock.patch("esi_leap.objects.event.Event.create")
    @mock.patch("esi_leap.common.rpc.VERSIONED_NOTIFIER")
    def test_emit_notification_empty_schema(self, mock_notifier, mock_event_create):
        self.config(notification_level="debug", group="notification")
        payload = self.TestNotificationPayloadEmptySchema(fake_field="123")
        notif = self.TestNotificationEmptySchema(
            event_type=notification.EventType(
                object="test_object",
                action="test",
                status=fields.NotificationStatus.ERROR,
            ),
            level=fields.NotificationLevel.ERROR,
            publisher=notification.NotificationPublisher(
                service="esi-leap-api", host="host"
            ),
            payload=payload,
        )

        mock_context = mock.Mock()
        notif.emit(mock_context)

        self._verify_notification(
            mock_notifier,
            mock_context,
            mock_event_create,
            expected_event_type="esi_leap.test_object.test.error",
            expected_payload={
                "esi_leap_object.name": "TestNotificationPayloadEmptySchema",
                "esi_leap_object.data": {
                    "fake_field": "123",
                },
                "esi_leap_object.version": "1.0",
                "esi_leap_object.namespace": "esi_leap",
            },
            expected_publisher="esi-leap-api.host",
            notif_level=fields.NotificationLevel.ERROR,
        )

    def test_populate_schema(self):
        payload = self.TestNotificationPayload(
            an_extra_field="extra", an_optional_field=1
        )
        payload.populate_schema(test_obj=self.fake_obj)
        self.assertEqual("extra", payload.an_extra_field)
        self.assertEqual(1, payload.an_optional_field)
        self.assertEqual(self.fake_obj.fake_field_1, payload.fake_field_a)
        self.assertEqual(self.fake_obj.fake_field_2, payload.fake_field_b)

    def test_populate_schema_missing_required_obj_field(self):
        test_obj = self.TestObject(fake_field_1="populated")
        # this payload requires missing fake_field_b
        payload = self.TestNotificationPayload(an_extra_field="too extra")
        self.assertRaises(
            exception.NotificationSchemaKeyError,
            payload.populate_schema,
            test_obj=test_obj,
        )

    def test_populate_schema_nullable_field_auto_populates(self):
        """Test that nullable fields always end up in the payload."""
        test_obj = self.TestObject(fake_field_2=123)
        payload = self.TestNotificationPayload()
        payload.populate_schema(test_obj=test_obj)
        self.assertIsNone(payload.fake_field_a)

    def test_populate_schema_no_object_field(self):
        test_obj = self.TestObjectMissingField(fake_field_1="foo")
        payload = self.TestNotificationPayload()
        self.assertRaises(
            exception.NotificationSchemaKeyError,
            payload.populate_schema,
            test_obj=test_obj,
        )

    def test_event_type_with_status(self):
        event_type = notification.EventType(
            object="some_obj", action="some_action", status="success"
        )
        self.assertEqual(
            "esi_leap.some_obj.some_action.success", event_type.to_event_type_field()
        )

    def test_event_type_without_status_fails(self):
        event_type = notification.EventType(object="some_obj", action="some_action")
        self.assertRaises(NotImplementedError, event_type.to_event_type_field)

    def test_event_type_invalid_status_fails(self):
        self.assertRaises(
            ValueError,
            notification.EventType,
            object="some_obj",
            action="some_action",
            status="invalid",
        )

    def test_event_type_make_status_invalid(self):
        def make_status_invalid():
            event_type.status = "Roar"

        event_type = notification.EventType(
            object="test_object", action="test", status="start"
        )
        self.assertRaises(ValueError, make_status_invalid)
