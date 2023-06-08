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

from http import client as http_client

from esi_leap.common.i18n import _


class ESILeapException(Exception):
    msg_fmt = _('An unknown exception occurred.')
    code = http_client.INTERNAL_SERVER_ERROR
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.msg_fmt % kwargs
            except Exception:
                message = self.msg_fmt

        self.message = message
        super(ESILeapException, self).__init__(message)


class HTTPForbidden(ESILeapException):
    code = http_client.FORBIDDEN
    msg_fmt = _('Access was denied to %(rule)s.')


class HTTPResourceForbidden(ESILeapException):
    code = http_client.FORBIDDEN
    msg_fmt = _('Access was denied to %(resource_type)s %(resource)s.')


class LeaseNoPermission(ESILeapException):
    msg_fmt = _('You do not have permissions on '
                'lease %(lease_uuid)s.')


class LeaseDuplicateName(ESILeapException):
    msg_fmt = _('Duplicate leases with name %(name)s.')


class LeaseNotActive(ESILeapException):
    msg_fmt = _('Lease with name or uuid %(lease_id)s not active.')


class LeaseNotFound(ESILeapException):
    msg_fmt = _('Lease with name or uuid %(lease_id)s not found.')


class LeaseNoOfferUUID(ESILeapException):
    msg_fmt = _('Cannot create lease without parameter offer_uuid.')


class LeaseNoTimeAvailabilities(ESILeapException):
    msg_fmt = _('Lease %(lease_uuid)s has no availabilities at given '
                'time range %(start_time)s, %(end_time)s.')


class OfferNoPermission(ESILeapException):
    msg_fmt = _('You do not have permissions on '
                'offer %(offer_uuid)s.')


class OfferDuplicateName(ESILeapException):
    msg_fmt = _('Duplicate offers with name %(name)s.')


class OfferNotFound(ESILeapException):
    msg_fmt = _('Offer with name or uuid %(offer_uuid)s not found.')


class OfferNoTimeAvailabilities(ESILeapException):
    msg_fmt = _('Offer %(offer_uuid)s has no availabilities at given '
                'time range %(start_time)s, %(end_time)s.')


class OfferNotAvailable(ESILeapException):
    msg_fmt = _('Offer %(offer_uuid)s does not have status '
                '"available". Got offer status "%(status)s".')


class ProjectNoPermission(ESILeapException):
    msg_fmt = _('You do not have permissions on project %(project_id)s.')


class ProjectNoSuchName(ESILeapException):
    msg_fmt = _('No project named %(name)s.')


class ResourceTimeConflict(ESILeapException):
    msg_fmt = ('Time conflict for %(resource_type)s %(resource_uuid)s.')


class ResourceNoPermission(ESILeapException):
    msg_fmt = _('You do not have permissions on '
                '%(resource_type)s %(resource_uuid)s.')


class ResourceNoPermissionTime(ESILeapException):
    msg_fmt = _('You do not have permissions on '
                '%(resource_type)s %(resource_uuid)s for the time range '
                '%(start_time)s - %(end_time)s.')


class ResourceTypeUnknown(ESILeapException):
    msg_fmt = _('%(resource_type)s resource type unknown.')


class InvalidTimeAPICommand(ESILeapException):
    msg_fmt = _('Attempted to get %(resource)s resource without providing '
                'both a valid Start Time and End Time. '
                'Start Time must be strictly less than End Time. '
                'Got %(start_time)s, %(end_time)s.')


class InvalidAvailabilityAPICommand(ESILeapException):
    msg_fmt = _('Attempted to get an offer resource without providing '
                'both a valid Availability Start Time and Availability '
                'End Time. Availability Start Time must be strictly '
                'less than Availability End Time. '
                'Got %(a_start)s, %(a_end)s.')


class InvalidTimeRange(ESILeapException):
    msg_fmt = _('Attempted to create %(resource)s resource with an invalid '
                'Start Time and End Time. Start Time must be strictly less '
                'than End Time. Got %(start_time)s, %(end_time)s.')


class NodeNotFound(ESILeapException):
    msg_fmt = _('Encountered an error fetching info for node %(uuid)s '
                '(%(resource_type)s): %(err)s')


class NotificationPayloadError(ESILeapException):
    _msg_fmt = _("Payload not populated when trying to send notification "
                 "\"%(class_name)s\"")


class NotificationSchemaObjectError(ESILeapException):
    _msg_fmt = _("Expected object %(obj)s when populating notification payload"
                 " but got object %(source)s")


class NotificationSchemaKeyError(ESILeapException):
    _msg_fmt = _("Object %(obj)s doesn't have the field \"%(field)s\" "
                 "required for populating notification schema key "
                 "\"%(key)s\"")
