"""LDAP sync related handlers."""

from django.db.models import signals
from django.dispatch import receiver

from modoboa.core import models as core_models
from modoboa.parameters import tools as param_tools


@receiver(signals.post_save, sender=core_models.User)
def sync_ldap_account(sender, instance, created, **kwargs):
    """Create/modify a new LDAP account if needed."""
    config = dict(param_tools.get_global_parameters("core"))
    if not config["ldap_enable_sync"]:
        return
    from . import lib
    if created:
        return
    update_fields = kwargs.get("update_fields")
    if update_fields and "last_login" in update_fields:
        return
    lib.update_ldap_account(instance, config)
