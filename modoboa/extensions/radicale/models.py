"""
Radicale extension models.
"""
from __future__ import unicode_literals

import os

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _

from modoboa.extensions.admin.models import Domain
from modoboa.lib import parameters


@python_2_unicode_compatible
class Calendar(models.Model):

    """Abstract calendar definition."""

    name = models.CharField(max_length=200)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    @property
    def path(self):
        """Return the calendar path."""
        raise NotImplementedError

    @property
    def url(self):
        """Return the calendar URL."""
        if not hasattr(self, "_url"):
            self._url = os.path.join(
                parameters.get_admin("SERVER_LOCATION"),
                self.path
            )
        return self._url

    @property
    def tags(self):
        """Return calendar tags."""
        raise NotImplementedError

    @property
    def owner(self):
        """Return calendar owner."""
        raise NotImplementedError


class UserCalendarManager(models.Manager):

    """Custom UserCalendar manager."""

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
    def path(self):
        """Return the calendar path.

        <domain>/user/<localpart>/<name>
        """
        if not hasattr(self, "_path"):
            self._path = "%s/user/%s/%s" % (
                self.mailbox.domain.name, self.mailbox.address, self.name
            )
        return self._path

    @property
    def tags(self):
        return [{"name": "user", "label": _("User"), "type": "cal"}]

    @property
    def owner(self):
        return self.mailbox.user


class SharedCalendarManager(models.Manager):

    """Custom SharedCalendar manager."""

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
    def path(self):
        """Return the calendar path.

        <domain>/shared/<name>
        """
        if not hasattr(self, "_path"):
            self._path = "%s/shared/%s" % (self.domain.name, self.name)
        return self._path

    @property
    def tags(self):
        return [{"name": "shared", "label": _("Shared"), "type": "cal"}]

    @property
    def owner(self):
        """Return calendar owner."""
        return self.domain


@python_2_unicode_compatible
class AccessRule(models.Model):

    """Access rules to user calendars."""

    mailbox = models.ForeignKey("admin.Mailbox")
    read = models.BooleanField(default=False)
    write = models.BooleanField(default=False)
    calendar = models.ForeignKey(UserCalendar, related_name="rules")
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('mailbox', 'calendar')

    def __str__(self):
        access = "r" if self.read else ""
        access += "w" if self.write else ""
        return "%s access rule to %s -> " \
            % (self.mailbox, self.calendar, access if access else "no access")
