"""
Radicale extension models.
"""
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _
from modoboa.extensions.admin.models import Domain


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
    def url(self):
        """Return the calendar URL"""
        raise NotImplementedError

    @property
    def type(self):
        """Return calendar type"""
        raise NotImplementedError


class UserCalendarManager(models.Manager):
    """Custom UserCalendar manager.
    """

    def get_for_admin(self, admin):
        """Return the list of calendars this admin can access.

        :param ``core.User`` admin: administrator
        """
        domains = Domain.objects.get_for_admin(admin)
        return self.get_query_set().filter(mailbox__domain__in=domains)


class UserCalendar(Calendar):
    """User calendar.

    We associate the calendar to a mailbox because we need to access
    the related domain.

    """
    mailbox = models.ForeignKey("admin.Mailbox")

    objects = UserCalendarManager()

    @property
    def url(self):
        """Return the calendar URL.

        <domain>/user/<localpart>/<name>
        """
        return "%s/user/%s/%s" % (
            self.mailbox.domain.name, self.mailbox.address, self.name
        )

    @property
    def type(self):
        return _("user")


class SharedCalendarManager(models.Manager):
    """Custom SharedCalendar manager.
    """

    def get_for_admin(self, admin):
        """Return the list of calendars this admin can access.

        :param ``core.User`` admin: administrator
        """
        domains = Domain.objects.get_for_admin(admin)
        return self.get_query_set().filter(domain__in=domains)


class SharedCalendar(Calendar):
    """Shared calendar.

    A shared calendar is associated to a domain and is readable and
    writable by all domain members.

    """
    domain = models.ForeignKey("admin.Domain")

    objects = SharedCalendarManager()

    @property
    def url(self):
        """Return the calendar URL.

        <domain>/shared/<name>
        """
        return "%s/shared/%s" % (
            self.domain.name, self.name
        )

    @property
    def type(self):
        return _("shared")
