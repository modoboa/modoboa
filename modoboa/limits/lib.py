# coding: utf-8
"""
:mod:`lib` --- public functions
-------------------------------

"""
from django.utils.translation import ugettext as _

from modoboa.lib.exceptions import ModoboaException

from .models import LimitsPool


class LimitReached(ModoboaException):
    http_code = 403

    def __init__(self, limit):
        self.limit = limit

    def __str__(self):
        return _("%s: limit reached") % self.limit.label


class UnsufficientResource(ModoboaException):
    http_code = 424

    def __init__(self, limit):
        self.limit = limit

    def __str__(self):
        return _("Not enough resources")


class BadLimitValue(ModoboaException):
    http_code = 400


def inc_limit_usage(user, lname):
    """Increase a given limit usage."""
    try:
        user.limitspool.inc_curvalue(lname)
    except LimitsPool.DoesNotExist:
        pass


def dec_limit_usage(user, lname):
    if user is None:
        return
    try:
        user.limitspool.dec_curvalue(lname)
    except LimitsPool.DoesNotExist:
        pass
