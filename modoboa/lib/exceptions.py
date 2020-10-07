"""
:mod:`exceptions` --- Custom Modoboa exceptions
-----------------------------------------------

"""

from django.utils.translation import ugettext as _


class ModoboaException(Exception):
    """
    Base class for Modoboa custom exceptions.
    """
    http_code = None

    def __init__(self, *args, **kwargs):
        if "http_code" in kwargs:
            self.http_code = kwargs["http_code"]
            del kwargs["http_code"]
        super(ModoboaException, self).__init__(*args, **kwargs)


class InternalError(ModoboaException):
    """
    Use this exception for system errors, missing dependencies, etc.
    """
    http_code = 500


class BadRequest(ModoboaException):
    """
    Use this exception when received data doesn't validate a specific
    format (example: wrong CSV line) or doesn't respect validation
    rules.
    """
    http_code = 400


class NotFound(ModoboaException):
    """
    Use this exception to indicate the requested resource could not be
    found.
    """
    http_code = 404


class Conflict(ModoboaException):
    """
    Use this exception to indicate that the request could not be
    processed because of conflict in the request.
    """
    http_code = 409


class PermDeniedException(ModoboaException):
    """
    Use this exception when a user tries to do something he is not
    allowed to.
    """
    http_code = 403

    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        if self.msg:
            return _("Permission denied: %s" % self.msg)
        return _("Permission denied")
