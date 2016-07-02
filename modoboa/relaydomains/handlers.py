"""Django signal handlers for relaydomains."""

from django.db.models import signals
from django.dispatch import receiver

from modoboa.admin import models as admin_models
from modoboa.admin.signals import use_external_recipients
from modoboa.lib.email_utils import split_mailbox

from . import models


@receiver(use_external_recipients)
def check_relaydomain_alias(sender, **kwargs):
    """Allow the creation of an alias on a relaydomain."""
    recipient = kwargs.get("recipients")
    if not recipient:
        return
    localpart, domain = split_mailbox(recipient)
    if not (models.RelayDomain.objects.select_related().filter(
            domain__name=domain).exists()):
        return False
    if (admin_models.Mailbox.objects.select_related("domain").filter(
            domain__name=domain, address=localpart).exists()):
        return False
    return True


@receiver(signals.post_save, sender=admin_models.Domain)
def clean_domain(sender, instance, **kwargs):
    """Remove or create RelayDomain record if needed."""
    if kwargs.get("created"):
        return
    has_relaydom = hasattr(instance, "relaydomain")
    if instance.type == "domain" and has_relaydom:
        models.RelayDomain.objects.filter(domain=instance).delete()
    elif instance.type == "relaydomain" and not has_relaydom:
        # Make sure to create a RelayDomain instance since we can't do it
        # at form level...
        models.RelayDomain.objects.create(
            domain=instance, service=models.Service.objects.first())
