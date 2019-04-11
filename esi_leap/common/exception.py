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


class PolicyNotFound(ESILeapException):
    msg_fmt = _("Policy with uuid %(policy_uuid)s not found.")

class LeaseRequestNotFound(ESILeapException):
    msg_fmt = _("Lease request with uuid %(request_uuid)s not found.")

class NodeExists(ESILeapException):
    msg_fmt = _("Node with uuid %(node_uuid)s already exists.")

class NodeNotFound(ESILeapException):
    msg_fmt = _("Node with uuid %(node_uuid)s not found.")
