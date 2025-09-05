"""Amavis handlers."""

from django.db.models import signals
from django.dispatch import receiver
from django.utils.translation import gettext as _

from modoboa.admin import models as admin_models
from modoboa.core import signals as core_signals
from modoboa.lib import signals as lib_signals
from modoboa.parameters import tools as param_tools
from .lib import (
    create_user_and_policy,
    create_user_and_use_policy,
    delete_user,
    delete_user_and_policy,
    update_user_and_policy,
)
from .models import Policy, Users
from .sql_connector import SQLconnector


@receiver(signals.post_save, sender=admin_models.Domain)
def manage_domain_policy(sender, instance, **kwargs):
    """Create user and policy when a domain is added."""
    if kwargs.get("created"):
        create_user_and_policy(f"@{instance.name}")
    else:
        update_user_and_policy(f"@{instance.oldname}", f"@{instance.name}")


@receiver(signals.pre_delete, sender=admin_models.Domain)
def on_domain_deleted(sender, instance, **kwargs):
    """Delete user and policy for domain."""
    delete_user_and_policy(f"@{instance.name}")


@receiver(signals.post_save, sender=admin_models.DomainAlias)
def on_domain_alias_created(sender, instance, **kwargs):
    """Create user and use domain policy for domain alias."""
    if not kwargs.get("created"):
        return
    create_user_and_use_policy(f"@{instance.name}", f"@{instance.target.name}")


@receiver(signals.pre_delete, sender=admin_models.DomainAlias)
def on_domain_alias_deleted(sender, instance, **kwargs):
    """Delete user for domain alias."""
    delete_user(f"@{instance.name}")


@receiver(signals.post_save, sender=admin_models.Mailbox)
def on_mailbox_modified(sender, instance, **kwargs):
    """Update amavis records if address has changed."""
    condition = (
        not param_tools.get_global_parameter("manual_learning")
        or not hasattr(instance, "old_full_address")
        or instance.full_address == instance.old_full_address
    )
    if condition:
        return
    try:
        user = Users.objects.select_related("policy").get(
            email=instance.old_full_address
        )
    except Users.DoesNotExist:
        return
    full_address = instance.full_address
    user.email = full_address
    user.policy.policy_name = full_address[:32]
    user.policy.sa_username = full_address
    user.policy.save()
    user.save()


@receiver(signals.pre_delete, sender=admin_models.Mailbox)
def on_mailbox_deleted(sender, instance, **kwargs):
    """Clean amavis database when a mailbox is removed."""
    if not param_tools.get_global_parameter("manual_learning"):
        return
    delete_user_and_policy(f"@{instance.full_address}")


@receiver(signals.post_save, sender=admin_models.AliasRecipient)
def on_aliasrecipient_created(sender, instance, **kwargs):
    """Create amavis record for the new alias recipient.

    FIXME: how to deal with distibution lists ?
    """
    conf = dict(param_tools.get_global_parameters("amavis"))
    condition = (
        not conf["manual_learning"]
        or not conf["user_level_learning"]
        or not instance.r_mailbox
        or instance.alias.type != "alias"
    )
    if condition:
        return
    policy = Policy.objects.filter(policy_name=instance.r_mailbox.full_address).first()
    if policy:
        # Use mailbox policy for this new alias. We update or create
        # to handle the case where an account is being replaced by an
        # alias (when it is disabled).
        email = instance.alias.address
        Users.objects.update_or_create(
            email=email, defaults={"policy": policy, "fullname": email, "priority": 7}
        )


@receiver(signals.pre_delete, sender=admin_models.Alias)
def on_mailboxalias_deleted(sender, instance, **kwargs):
    """Clean amavis database when an alias is removed."""
    if not param_tools.get_global_parameter("manual_learning"):
        return
    if instance.address.startswith("@"):
        # Catchall alias, do not remove domain entry accidentally...
        return
    aliases = [instance.address]
    Users.objects.filter(email__in=aliases).delete()


@receiver(core_signals.get_top_notifications)
def check_for_pending_requests(sender, include_all, **kwargs):
    """Check if release requests are pending."""
    request = lib_signals.get_request()
    condition = (
        param_tools.get_global_parameter("user_can_release")
        or request.user.role == "SimpleUsers"
    )
    if condition:
        return []

    nbrequests = SQLconnector(user=request.user).get_pending_requests()
    if not nbrequests:
        return [{"id": "nbrequests", "counter": 0}] if include_all else []

    url = "/user/quarantine?requests=1"
    return [
        {
            "id": "nbrequests",
            "url": url,
            "text": _("Pending requests"),
            "counter": nbrequests,
            "color": "error",
            "target": "all",
        }
    ]
