# coding: utf-8
"""
:mod:`exceptions` --- Webmail custom exceptions
-----------------------------------------------

"""
import re
from django.utils.translation import ugettext as _
from modoboa.lib.exceptions import ModoboaException, InternalError


class WebmailInternalError(InternalError):
    errorexpr = re.compile(r'\[([^\]]+)\]\s*([^\.]+)')

    def __init__(self, reason, ajax=False):
        match = WebmailInternalError.errorexpr.match(reason)
        if not match:
            self.reason = reason
        else:
            self.reason = "%s: %s" % (_("Server response"), match.group(2))
        self.ajax = ajax

    def __str__(self):
        return self.reason


class UnknownAction(ModoboaException):
    """
    Use this exception when the webmail encounter an unknown action.
    """
    http_code = 404

    def __init__(self):
        super(UnknownAction, self).__init__(_("Unknown action"))


class ImapError(ModoboaException):
    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return str(self.reason)
