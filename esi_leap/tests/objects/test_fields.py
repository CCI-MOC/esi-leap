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

from esi_leap.objects import fields
from esi_leap.tests import base


# FlexibleDict borrowed from Ironic
class TestFlexibleDictField(base.TestCase):

    def setUp(self):
        super(TestFlexibleDictField, self).setUp()
        self.field = fields.FlexibleDictField()

    def test_coerce(self):
        d = {'foo_1': 'bar', 'foo_2': 2, 'foo_3': [], 'foo_4': {}}
        self.assertEqual(d, self.field.coerce('obj', 'attr', d))
        self.assertEqual({'foo': 'bar'},
                         self.field.coerce('obj', 'attr', '{"foo": "bar"}'))

    def test_coerce_bad_values(self):
        self.assertRaises(TypeError, self.field.coerce, 'obj', 'attr', 123)
        self.assertRaises(TypeError, self.field.coerce, 'obj', 'attr', True)

    def test_coerce_nullable_translation(self):
        # non-nullable
        self.assertRaises(ValueError, self.field.coerce, 'obj', 'attr', None)

        # nullable
        self.field = fields.FlexibleDictField(nullable=True)
        self.assertEqual({}, self.field.coerce('obj', 'attr', None))


# NotificationLevelField borrowed from Ironic
class TestNotificationLevelField(base.TestCase):

    def setUp(self):
        super(TestNotificationLevelField, self).setUp()
        self.field = fields.NotificationLevelField()

    def test_coerce_good_value(self):
        self.assertEqual(fields.NotificationLevel.WARNING,
                         self.field.coerce('obj', 'attr', 'warning'))

    def test_coerce_bad_value(self):
        self.assertRaises(ValueError, self.field.coerce, 'obj', 'attr',
                          'not_a_priority')


# NotificationStatusField borrowed from Ironic
class TestNotificationStatusField(base.TestCase):

    def setUp(self):
        super(TestNotificationStatusField, self).setUp()
        self.field = fields.NotificationStatusField()

    def test_coerce_good_value(self):
        self.assertEqual(fields.NotificationStatus.START,
                         self.field.coerce('obj', 'attr', 'start'))

    def test_coerce_bad_value(self):
        self.assertRaises(ValueError, self.field.coerce, 'obj', 'attr',
                          'not_a_priority')
