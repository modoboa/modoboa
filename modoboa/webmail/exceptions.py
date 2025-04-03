"""Webmail custom exceptions."""

import re

from django.utils.translation import gettext as _

from modoboa.lib.exceptions import ModoboaException, InternalError


class WebmailInternalError(InternalError):
    errorexpr = re.compile(r"\[([^\]]+)\]\s*([^\.]+)")

    def __init__(self, reason, ajax=False):
        match = WebmailInternalError.errorexpr.match(reason)
        if not match:
            self.reason = reason
        else:
            self.reason = f"{_('Server response')}: {match.group(2)}"
        self.ajax = ajax

    def __str__(self):
        return self.reason


class ImapError(ModoboaException):

    http_code = 500

    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return str(self.reason)
