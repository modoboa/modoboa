"""Radicale signals handlers."""

try:
    from secrets import token_hex
except ImportError:
    from os import urandom

    def token_hex(nbytes=None):
        return urandom(nbytes).hex()


from django.db.models import signals
from django.dispatch import receiver

from modoboa.core import signals as core_signals

from . import models


PERMISSIONS = [
    ("calendars", "usercalendar", "add_usercalendar"),
    ("calendars", "usercalendar", "change_usercalendar"),
    ("calendars", "usercalendar", "delete_usercalendar"),
    ("calendars", "sharedcalendar", "add_sharedcalendar"),
    ("calendars", "sharedcalendar", "change_sharedcalendar"),
    ("calendars", "sharedcalendar", "delete_sharedcalendar"),
]

ROLES_PERMISSIONS = {
    "DomainAdmins": PERMISSIONS,
    "Resellers": PERMISSIONS,
    "SimpleUsers": [
        ("calendars", "usercalendar", "add_usercalendar"),
        ("calendars", "usercalendar", "change_usercalendar"),
        ("calendars", "usercalendar", "delete_usercalendar"),
    ],
}


@receiver(core_signals.extra_role_permissions)
def extra_permissions(sender, role, **kwargs):
    """Extra permissions."""
    return ROLES_PERMISSIONS.get(role, [])


@receiver(signals.pre_save, sender=models.UserCalendar)
def set_user_calendar_path(sender, instance, **kwargs):
    """Set path at creation."""
    if instance.pk:
        return
    instance._path = f"{instance.mailbox.full_address}/{instance.name}"
    if not instance.access_token:
        instance.access_token = token_hex(16)


@receiver(signals.pre_save, sender=models.SharedCalendar)
def set_shared_calendar_path(sender, instance, **kwargs):
    """Set path at creation."""
    if instance.pk:
        return
    instance._path = f"{instance.domain.name}/{instance.name}"
    if not instance.access_token:
        instance.access_token = token_hex(16)
