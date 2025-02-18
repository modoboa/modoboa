"""Alert related models."""

from django.db import models
from django.utils import timezone

from reversion import revisions as reversion

from .. import constants


class AlarmQuerySet(models.QuerySet):
    """Custom queryset for Alarm."""

    def opened(self):
        """Return opened alarms."""
        return self.filter(status=constants.ALARM_OPENED)


class Alarm(models.Model):
    """A simple alarm to attach to a domain and/or mailbox."""

    domain = models.ForeignKey(
        "admin.Domain",
        on_delete=models.CASCADE,
        related_name="alarms",
        blank=True,
        null=True,
    )
    mailbox = models.ForeignKey(
        "admin.Mailbox",
        on_delete=models.SET_NULL,
        related_name="alarms",
        null=True,
        blank=True,
    )
    created = models.DateTimeField(default=timezone.now)
    closed = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(
        default=constants.ALARM_OPENED, choices=constants.ALARM_STATUSES, db_index=True
    )

    title = models.TextField()
    internal_name = models.CharField(max_length=120)

    objects = models.Manager.from_queryset(AlarmQuerySet)()

    class Meta:
        ordering = ["created"]

    def __str__(self):
        return f"[{self.created}] {self.domain} - {self.get_status_display()}"

    def close(self):
        """Close this alarm."""
        self.status = constants.ALARM_CLOSED
        self.closed = timezone.now()
        self.save()

    def reopen(self):
        """Reopen this alarm."""
        self.status = constants.ALARM_OPENED
        self.closed = None
        self.save()


reversion.register(Alarm)
