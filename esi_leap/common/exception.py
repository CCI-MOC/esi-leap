from esi_leap.common.i18n import _


class ESILeapException(Exception):
    msg_fmt = _("An unknown exception occurred.")
    code = 500
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
            except Exception as e:
                print e
                message = self.msg_fmt

        self.message = message
        super(ESILeapException, self).__init__(message)


class LeaseRequestIncorrectStatus(ESILeapException):
    msg_fmt = _("Lease request %(request_uuid)s has a status of %(status)s "
                ", but should have a status of %(actual_status)s.")


class LeaseRequestNoPermission(ESILeapException):
    msg_fmt = _("You do not have permissions on "
                "lease request %(request_uuid)s.")


class LeaseRequestNodeUnavailable(ESILeapException):
    msg_fmt = _("Lease request %(request_uuid)s cannot be fulfilled, "
                "as nodes are unavailable.")


class LeaseRequestNotFound(ESILeapException):
    msg_fmt = _("Lease request %(request_uuid)s not found.")


class LeaseRequestUnfulfilled(ESILeapException):
    msg_fmt = _("Lease request %(request_uuid)s was fulfilled, "
                "but no nodes were assigned.")


class LeaseRequestWrongFulfillStatus(ESILeapException):
    msg_fmt = _("Lease request %(request_uuid)s must have a status of "
                "pending to be fulfilled, but it has a status of %(status)s.")


class NodeExists(ESILeapException):
    msg_fmt = _("Node %(node_uuid)s already exists.")


class NodeNoPermission(ESILeapException):
    msg_fmt = _("You do not have permissions on node %(node_uuid)s.")


class NodeNotFound(ESILeapException):
    msg_fmt = _("Node %(node_uuid)s not found.")


class PolicyNoPermission(ESILeapException):
    msg_fmt = _("You do not have permissions on policy %(policy_uuid)s.")


class PolicyNotFound(ESILeapException):
    msg_fmt = _("Policy %(policy_uuid)s not found.")
