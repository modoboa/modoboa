"""
Radicale extension models.
"""
from __future__ import unicode_literals

import abc
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Calendar(models.Model):
    """Abstract calendar definition.
    """
    name = models.CharField(max_length=200)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    @property
    @abc.abstractmethod
    def url(self):
        """Return the calendar URL"""


class UserCalendar(Calendar):
    """User calendar.

    We associate the calendar to a mailbox because we need to access
    the related domain.

    """
    mailbox = models.ForeignKey("admin.Mailbox")

    @property
    def url(self):
        """Return the calendar URL.

        <domain>/user/<localpart>/<name>
        """
        return "%s/user/%s/%s" % (
            self.mailbox.domain.name, self.mailbox.address, self.name
        )


class SharedCalendar(Calendar):
    """Shared calendar.

    A shared calendar is associated to a domain and is readable and
    writable by all domain members.

    """
    domain = models.ForeignKey("admin.Domain")

    @property
    def url(self):
        """Return the calendar URL.

        <domain>/shared/<name>
        """
        return "%s/shared/%s" % (
            self.mailbox.domain.name, self.name
        )
