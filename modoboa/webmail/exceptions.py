"""Webmail custom exceptions."""

import re

from django.utils.translation import gettext as _

from modoboa.lib.exceptions import ModoboaException, InternalError


class WebmailInternalError(InternalError):
    errorexpr = re.compile(r"\[([^\]]+)\]\s*([^\.]+)")

    def __init__(self, reason, ajax=False):
        # imaplib returns server responses as bytes
        if isinstance(reason, bytes):
            reason = reason.decode(errors="replace")
        else:
            reason = str(reason)
        match = WebmailInternalError.errorexpr.match(reason)
        if not match:
            self.reason = reason
        else:
            self.reason = f"{_('Server response')}: {match.group(2)}"
        self.ajax = ajax

    def __str__(self):
        return self.reason


class MailboxOperationError(WebmailInternalError):
    """The IMAP server refused an operation on a mailbox.

    The mailbox already exists, does not exist, permission denied...:
    this is a user error, reported with the server's message.
    """

    http_code = 400


class ImapError(ModoboaException):

    http_code = 500

    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return str(self.reason)


class InvalidImapArgument(ImapError):
    """A user supplied value cannot be safely passed to the IMAP server."""

    http_code = 400
