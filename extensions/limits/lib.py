# coding: utf-8
"""
:mod:`lib` --- public functions
-------------------------------

"""
from django.contrib.auth.models import Group
from django.utils.translation import ugettext as _
from modoboa.lib.exceptions import ModoboaException

class LimitReached(ModoboaException):
    def __init__(self, limit):
        self.limit = limit

    def __str__(self):
        return "%s reached" % self.limit.name

class UnsifficientResource(ModoboaException):
    def __init__(self, limit):
        self.limit = limit

    def __str__(self):
        return _("Not enough resource into your pool")

class BadLimitValue(ModoboaException):
    pass

def is_reseller(user):
    """Tell if a user is a reseller or not

    :param user: a User object
    :return: True if the user is a reseller, False otherwise.
    """
    grp = Group.objects.get(name="Resellers")
    return grp in user.groups.all()
