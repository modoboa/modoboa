# coding: utf-8
"""
:mod:`exceptions` --- Custom Modoboa exceptions
-----------------------------------------------

"""
from django.utils.translation import ugettext as _

class ModoboaException(Exception):
    pass

class PermDeniedException(ModoboaException):
    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        if self.msg:
            return _("Permission denied: %s" % self.msg)
        return _("Permission denied")

class NeedsMailboxException(ModoboaException):
    pass
                              
