# coding: utf-8
"""
:mod:`exceptions` --- Custom exceptions of the admin. application
-----------------------------------------------------------------
"""

from modoboa.lib.exceptions import ModoboaException

class AdminError(ModoboaException):
    """
    Just a Custom exception to identify errors coming from the admin
    application.
    """
    pass

