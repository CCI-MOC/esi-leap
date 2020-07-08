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

import ast
import six

from oslo_versionedobjects import fields as object_fields


class DateTimeField(object_fields.DateTimeField):
    def __init__(self, **kwargs):
        super(DateTimeField, self).__init__(False, **kwargs)


# FlexibleDict borrowed from Ironic
class FlexibleDict(object_fields.FieldType):
    @staticmethod
    def coerce(obj, attr, value):
        if isinstance(value, six.string_types):
            value = ast.literal_eval(value)
        return dict(value)


class FlexibleDictField(object_fields.AutoTypedField):
    AUTO_TYPE = FlexibleDict()

    def _null(self, obj, attr):
        if self.nullable:
            return {}
        super(FlexibleDictField, self)._null(obj, attr)


class IntegerField(object_fields.IntegerField):
    pass


class ListOfObjectsField(object_fields.ListOfObjectsField):
    pass


class ObjectField(object_fields.ObjectField):
    pass


class StringField(object_fields.StringField):
    pass


class UUIDField(object_fields.UUIDField):
    pass
