"""Django signal handlers for admin."""

from django.db.models import signals
from django.dispatch import receiver

from modoboa.core import signals as core_signals

from . import models
from . import postfix_maps


@receiver(signals.post_save, sender=models.Domain)
def update_domain_mxs_and_mailboxes(sender, instance, **kwargs):
    """Update associated MXs and mailboxes."""
    if kwargs.get("created"):
        return
    instance.mailbox_set.filter(use_domain_quota=True).update(
        quota=instance.quota)
    if instance.old_mail_homes is None:
        return
    qset = (
        models.Quota.objects.filter(
            username__contains="@{}".format(instance.oldname))
    )
    for q in qset:
        username = q.username.replace(
            "@{}".format(instance.oldname), "@{}".format(instance.name))
        models.Quota.objects.create(
            username=username, bytes=q.bytes, messages=q.messages)
        q.delete()
    for mb in instance.mailbox_set.all():
        mb.rename_dir(instance.old_mail_homes[mb.pk])


@receiver(signals.post_save, sender=models.DomainAlias)
def create_alias_for_domainalias(sender, instance, **kwargs):
    """Create a dedicated alias for domain alias."""
    if not kwargs.get("created"):
        return
    alias = models.Alias.objects.create(
        address=u"@{}".format(instance.name), enabled=True, internal=True)
    models.AliasRecipient.objects.create(
        address=u"@{}".format(instance.target.name), alias=alias)


@receiver(signals.post_delete, sender=models.DomainAlias)
def remove_alias_for_domainalias(sender, instance, **kwargs):
    """Remove the alias associated to domain alias."""
    models.Alias.objects.filter(
        address=u"@{}".format(instance.name)).delete()


@receiver(signals.post_save, sender=models.Mailbox)
def manage_alias_for_mailbox(sender, instance, **kwargs):
    """Create or update a "self alias" for mailbox (catchall)."""
    if kwargs.get("created"):
        alias, created = models.Alias.objects.get_or_create(
            address=instance.full_address, domain=instance.domain,
            internal=True)
        models.AliasRecipient.objects.create(
            address=instance.full_address, alias=alias, r_mailbox=instance)
        return
    old_address = getattr(instance, "old_full_address", None)
    if old_address is None or old_address == instance.full_address:
        return
    alr = models.AliasRecipient.objects.get(
        alias__address=old_address, address=old_address,
        r_mailbox=instance, alias__internal=True)
    alr.address = instance.full_address
    alr.save()
    alr.alias.address = instance.full_address
    alr.alias.save()


@receiver(signals.pre_delete, sender=models.Mailbox)
def mailbox_deleted_handler(sender, **kwargs):
    """``Mailbox`` pre_delete signal receiver

    In order to properly handle deletions (ie. we don't want to leave
    orphan records into the db), we define this custom receiver.

    It manually removes the mailbox from the aliases it is linked to
    and then remove all empty aliases.
    """
    from modoboa.lib import events
    from modoboa.lib.permissions import ungrant_access_to_object

    mb = kwargs['instance']
    events.raiseEvent("MailboxDeleted", mb)
    ungrant_access_to_object(mb)
    for ralias in mb.aliasrecipient_set.select_related("alias"):
        alias = ralias.alias
        ralias.delete()
        if not alias.aliasrecipient_set.exists():
            alias.delete()


@receiver(signals.post_delete, sender=models.Mailbox)
def remove_alias_for_mailbox(sender, instance, **kwargs):
    """Remove "self alias" for this mailbox."""
    models.Alias.objects.filter(
        address=instance.full_address).delete()


@receiver(core_signals.register_postfix_maps)
def register_postfix_maps(sender, **kwargs):
    """Register admin map files."""
    return [
        postfix_maps.DomainsMap, postfix_maps.DomainsAliasesMap,
        postfix_maps.AliasesMap, postfix_maps.MaintainMap,
        postfix_maps.SenderLoginAliasMap, postfix_maps.SenderLoginMailboxMap,
        postfix_maps.SenderLoginMailboxExtraMap
    ]
