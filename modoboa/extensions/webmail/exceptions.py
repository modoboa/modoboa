# coding: utf-8
"""
:mod:`exceptions` --- Webmail custom exceptions
-----------------------------------------------

"""
import re
from django.utils.translation import ugettext as _
from modoboa.lib.exceptions import ModoboaException

class WebmailError(ModoboaException):
    errorexpr = re.compile("\[([^\]]+)\]\s*([^\.]+)")

    def __init__(self, reason, ajax=False):
        match = WebmailError.errorexpr.match(reason)
        if not match:
            self.reason = reason
        else:
            self.reason = "%s: %s" % (_("Server response"), match.group(2))
        self.ajax = ajax

    def __str__(self):
        return self.reason

class ImapError(ModoboaException):
    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return str(self.reason)
