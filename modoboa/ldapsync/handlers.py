"""LDAP sync related handlers."""

from django.db.models import signals
from django.dispatch import receiver

from modoboa.core import models as core_models
from modoboa.parameters import tools as param_tools

from . import lib


@receiver(signals.post_save, sender=core_models.User)
def sync_ldap_account(sender, instance, created, **kwargs):
    """Create/modify a new LDAP account if needed."""
    config = dict(param_tools.get_global_parameters("core"))
    if not config["ldap_enable_sync"]:
        return
    if created:
        return
    if instance.role != "SimpleUsers":
        return
    update_fields = kwargs.get("update_fields")
    if update_fields and "last_login" in update_fields:
        return
    lib.update_ldap_account(instance, config)


@receiver(signals.pre_delete, sender=core_models.User)
def delete_ldap_account(sender, instance, **kwargs):
    """Delete LDAP account if needed."""
    config = dict(param_tools.get_global_parameters("core"))
    if not config["ldap_enable_sync"]:
        return
    if instance.role != "SimpleUsers":
        return
    lib.delete_ldap_account(instance, config)
