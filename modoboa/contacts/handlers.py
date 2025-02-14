"""Webmail handlers."""

from django.db.models import signals
from django.dispatch import receiver

from modoboa.admin import models as admin_models

from . import models


@receiver(signals.post_save, sender=admin_models.Mailbox)
def create_addressbook(sender, instance, created, **kwargs):
    """Create default address book for new mailbox."""
    if not created:
        return
    models.AddressBook.objects.create(
        user=instance.user, name="Contacts", _path="contacts"
    )
