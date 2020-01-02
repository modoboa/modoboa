"""
:mod:`lib` --- public functions
-------------------------------

"""

from django.utils.translation import ugettext as _

from modoboa.lib.exceptions import ModoboaException


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


def allocate_resources_from_user(limit, user, value):
    """Allocate resource using an existing user.

    When a reseller creates a domain administrator, he generally
    assigns him resource to create new objetcs. As a reseller may
    also be limited, the resource he gives is taken from its own
    pool.
    """
    ol = user.userobjectlimit_set.get(name=limit.name)
    if value == -1 and ol.max_value != -1:
        raise BadLimitValue(
            _("You're not allowed to define unlimited values")
        )

    if limit.max_value > -1:
        value -= limit.max_value
        if value == 0:
            return
    remain = ol.max_value - ol.current_value
    if value > remain:
        raise UnsufficientResource(ol)
    ol.max_value -= value
    ol.save()
