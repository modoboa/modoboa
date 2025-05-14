"""Django signal handlers for relaydomains."""

from django.db.models import signals
from django.dispatch import receiver

from modoboa.admin import models as admin_models, signals as admin_signals
from modoboa.core import signals as core_signals
from modoboa.lib.email_utils import split_mailbox
from modoboa.transport import models as tr_models
from . import lib, models, postfix_maps


@receiver(admin_signals.use_external_recipients)
def check_relaydomain_alias(sender, recipients, **kwargs):
    """Allow the creation of an alias on a relaydomain."""
    localpart, domain = split_mailbox(recipients)
    qset = admin_models.Domain.objects.filter(name=domain, type="relaydomain")
    if not qset.exists():
        return False
    qset = admin_models.Mailbox.objects.select_related("domain").filter(
        domain__name=domain, address=localpart
    )
    if qset.exists():
        return False
    return True


@receiver(signals.post_save, sender=admin_models.Domain)
def clean_domain(sender, instance, **kwargs):
    """Remove or create Transport record if needed."""
    if kwargs.get("created") or instance.type == "relaydomain":
        return
    tr_models.Transport.objects.filter(pattern=instance.name).delete()


@receiver(signals.post_delete, sender=admin_models.Domain)
def delete_transport(sender, instance, **kwargs):
    """Delete Transport instance if any."""
    tr_models.Transport.objects.filter(pattern=instance.name).delete()


@receiver(core_signals.register_postfix_maps)
def register_postfix_maps(sender, **kwargs):
    """Register postfix maps."""
    return [
        postfix_maps.RelayDomainsMap,
        postfix_maps.SplitedDomainsTransportMap,
        postfix_maps.RelayRecipientVerification,
    ]


@receiver(admin_signals.import_object)
def get_import_func(sender, objtype, **kwargs):
    """Return function used to import objtype."""
    if objtype == "relaydomain":
        return lib.import_relaydomain
    return None


@receiver(signals.post_save, sender=tr_models.Transport)
def update_recipient_access(sender, instance, **kwargs):
    """Create or delete recipient access rule."""
    if instance.service != "relay":
        return
    if instance._settings.get("relay_verify_recipients", False):
        models.RecipientAccess.objects.get_or_create(
            pattern=instance.pattern, defaults={"action": "reject_unverified_recipient"}
        )
    else:
        models.RecipientAccess.objects.filter(pattern=instance.pattern).delete()


@receiver(signals.post_delete, sender=tr_models.Transport)
def delete_recipient_access(sender, instance, **kwargs):
    """Delete recipient access rule."""
    if instance.service != "relay":
        return
    models.RecipientAccess.objects.filter(pattern=instance.pattern).delete()
