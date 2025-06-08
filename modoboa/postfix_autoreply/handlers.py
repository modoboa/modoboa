"""Django signal handlers for modoboa_postfix_autoreply."""

from django.db.models import signals
from django.dispatch import receiver

from modoboa.admin import models as admin_models
from modoboa.transport import models as tr_models

from . import models


@receiver(signals.post_save, sender=admin_models.Domain)
def manage_transport_entry(sender, instance, **kwargs):
    """Create or update a transport entry for this domain."""
    if kwargs.get("created"):
        tr_models.Transport.objects.get_or_create(
            pattern=f"autoreply.{instance}", service="autoreply"
        )
        return
    oldname = getattr(instance, "oldname", "None")
    if oldname is None or oldname == instance.name:
        return
    tr_models.Transport.objects.filter(pattern=f"autoreply.{oldname}").update(
        pattern=f"autoreply.{instance.name}"
    )
    qset = admin_models.AliasRecipient.objects.select_related(
        "alias", "r_mailbox"
    ).filter(
        alias__domain=instance, alias__internal=True, address__contains="@autoreply"
    )
    for alr in qset:
        alr.address = alr.address.replace(oldname, instance.name)
        alr.save()


@receiver(signals.post_delete, sender=admin_models.Domain)
def delete_transport_entry(sender, instance, **kwargs):
    """Delete a transport entry."""
    tr_models.Transport.objects.filter(pattern=f"autoreply.{instance}").delete()


@receiver(signals.post_save, sender=admin_models.Mailbox)
def rename_autoreply_alias(sender, instance, **kwargs):
    """Rename AR alias if needed."""
    old_address = getattr(instance, "old_full_address", None)
    if old_address is None or old_address == instance.full_address:
        return
    admin_models.AliasRecipient.objects.filter(
        address__contains=f"{old_address}@autoreply"
    ).update(address=f"{instance.full_address}@autoreply.{instance.domain}")


@receiver(signals.post_delete, sender=admin_models.Mailbox)
def delete_autoreply_alias(sender, instance, **kwargs):
    """Delete alias."""
    admin_models.AliasRecipient.objects.filter(
        address=f"{instance.full_address}@autoreply.{instance.domain}"
    ).delete()


@receiver(signals.post_save, sender=models.ARmessage)
def manage_autoreply_alias(sender, instance, **kwargs):
    """Create or delete the alias."""
    ar_alias_address = f"{instance.mbox.full_address}@autoreply.{instance.mbox.domain}"
    admin_models.Alias.objects.get(
        address=instance.mbox.full_address, domain=instance.mbox.domain, internal=True
    )
    alias, created = admin_models.Alias.objects.get_or_create(
        address=instance.mbox.full_address, domain=instance.mbox.domain, internal=True
    )
    if instance.enabled:
        admin_models.AliasRecipient.objects.get_or_create(
            alias=alias, address=ar_alias_address
        )
    else:
        admin_models.AliasRecipient.objects.filter(address=ar_alias_address).delete()
