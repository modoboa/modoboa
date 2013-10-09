# coding: utf-8
"""
:mod:`lib` --- public functions
-------------------------------

"""
from django.utils.translation import ugettext as _
from modoboa.lib.exceptions import ModoboaException


class LimitReached(ModoboaException):
    def __init__(self, limit):
        self.limit = limit

    def __str__(self):
        return _("%s: limit reached") % self.limit.label


class UnsufficientResource(ModoboaException):
    def __init__(self, limit):
        self.limit = limit

    def __str__(self):
        return _("Not enough resources")


class BadLimitValue(ModoboaException):
    pass
