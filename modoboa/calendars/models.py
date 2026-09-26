"""Radicale extension models."""

import os
import unicodedata

from six.moves import urllib

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from modoboa.admin.models import Domain, Mailbox

from modoboa.lib import exceptions as lib_exceptions
from modoboa.parameters import tools as param_tools

#: Characters forbidden in calendar names. A name ends up verbatim in the
#: collection path and in the Radicale rights file (an INI file):
#: - path separators would change the path,
#: - Radicale (>= 3.8, validate_path_value = minimal) refuses paths
#:   containing any of :'"*?,
#: Control characters (newlines, NUL...) are refused too, they would let a
#: name break out of its value in the rights file.
CALENDAR_NAME_FORBIDDEN_CHARACTERS = "/\\:'\"*?,"


def calendar_name_validator(value):
    """Check that a calendar name can be used as a Radicale collection name."""
    if value in (".", "..") or any(
        char in CALENDAR_NAME_FORBIDDEN_CHARACTERS
        or unicodedata.category(char).startswith("C")
        for char in value
    ):
        raise ValidationError(
            _(
                "Calendar name cannot be . or .. nor contain control characters "
                "or any of: %(characters)s"
            )
            % {"characters": " ".join(CALENDAR_NAME_FORBIDDEN_CHARACTERS)},
            code="invalid",
        )


class Calendar(models.Model):
    """Abstract calendar definition."""

    name = models.CharField(max_length=200, validators=[calendar_name_validator])
    color = models.CharField(max_length=7, default="#3a87ad")
    _path = models.TextField()
    access_token = models.CharField(max_length=50)

    class Meta:
        abstract = True

    def __str__(self):
        return smart_str(self.name)

    @property
    def path(self):
        """Return the calendar path."""
        return self._path

    @property
    def encoded_path(self):
        """Return url encoded path."""
        return urllib.parse.quote(smart_str(self._path))

    @property
    def full_url(self):
        """Return the calendar URL."""
        if not hasattr(self, "_url"):
            server_location = param_tools.get_global_parameter("server_location")
            if not server_location:
                raise lib_exceptions.InternalError(
                    _("Server location is not set, please fix it.")
                )
            self._url = os.path.join(server_location, self._path)
        return self._url

    @property
    def share_url(self):
        """Return calendar share url."""
        return f"{self.full_url}?token={self.access_token}"

    @property
    def encoded_url(self):
        """Return encoded url."""
        if not hasattr(self, "_encoded_url"):
            server_location = param_tools.get_global_parameter("server_location")
            if not server_location:
                raise lib_exceptions.InternalError(
                    _("Server location is not set, please fix it.")
                )
            self._encoded_url = os.path.join(server_location, self.encoded_path)
        return self._encoded_url

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
        return self.get_queryset().filter(mailbox__domain__in=domains)


class UserCalendar(Calendar):
    """User calendar.

    We associate the calendar to a mailbox because we need to access
    the related domain.

    """

    mailbox = models.ForeignKey(Mailbox, on_delete=models.CASCADE)

    objects = UserCalendarManager()

    class Meta(Calendar.Meta):
        db_table = "radicale_usercalendar"
        constraints = [
            models.UniqueConstraint(
                fields=["mailbox", "name"], name="radicale_usercalendar_unique_name"
            )
        ]

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
        return self.get_queryset().filter(domain__in=domains)


class SharedCalendar(Calendar):
    """Shared calendar.

    A shared calendar is associated to a domain and is readable and
    writable by all domain members.

    """

    domain = models.ForeignKey(Domain, on_delete=models.CASCADE)

    objects = SharedCalendarManager()

    class Meta(Calendar.Meta):
        db_table = "radicale_sharedcalendar"
        constraints = [
            models.UniqueConstraint(
                fields=["domain", "name"], name="radicale_sharedcalendar_unique_name"
            )
        ]

    @property
    def owner(self):
        """Return calendar owner."""
        return self.domain


def get_free_path(model, path):
    """Return a collection path not used by any calendar of model.

    A calendar keeps its path when it is renamed, so the path built from
    a new calendar's name can already be used. Comparison ignores case,
    for case-insensitive filesystems and database collations.
    """
    candidate = path
    counter = 2
    while model.objects.filter(_path__iexact=candidate).exists():
        candidate = f"{path}-{counter}"
        counter += 1
    return candidate


def get_share_candidates(owner):
    """Return the mailboxes a user calendar can be shared with.

    :param owner: the ``Mailbox`` owning the calendar
    """
    return Mailbox.objects.filter(
        domain_id=owner.domain_id, domain__enabled=True, user__is_active=True
    ).exclude(pk=owner.pk)


class AccessRule(models.Model):
    """Access rules to user calendars."""

    mailbox = models.ForeignKey(Mailbox, on_delete=models.CASCADE)
    read = models.BooleanField(default=False)
    write = models.BooleanField(default=False)
    calendar = models.ForeignKey(
        UserCalendar, related_name="rules", on_delete=models.CASCADE
    )
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("mailbox", "calendar")
        db_table = "radicale_accessrule"

    def __str__(self):
        access = "r" if self.read else ""
        access += "w" if self.write else ""
        return smart_str(
            "{} access rule to {} -> {}".format(
                self.mailbox, self.calendar, access if access else "no access"
            )
        )
