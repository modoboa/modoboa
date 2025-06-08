"""Django signal handlers for limits."""

from django.contrib.contenttypes.models import ContentType
from django.db.models import signals
from django.dispatch import receiver

from modoboa.admin import models as admin_models
from modoboa.core import models as core_models, signals as core_signals
from modoboa.lib import permissions, signals as lib_signals
from modoboa.parameters import tools as param_tools
from . import lib, models, utils


@receiver(core_signals.can_create_object)
def check_object_limit(sender, context, **kwargs):
    """Check if user can create a new object."""
    if context.__class__.__name__ == "User":
        if not param_tools.get_global_parameter("enable_admin_limits"):
            return
        # FIXME: Useless?
        if context.is_superuser:
            return True
        if "klass" in kwargs:
            ct = ContentType.objects.get_for_model(kwargs.get("klass"))
            limits = context.userobjectlimit_set.filter(content_type=ct)
        else:
            limits = context.userobjectlimit_set.filter(name=kwargs["object_type"])
    elif context.__class__.__name__ == "Domain":
        if not param_tools.get_global_parameter("enable_domain_limits"):
            return
        object_type = kwargs.get("object_type")
        limits = context.domainobjectlimit_set.filter(name=object_type)
    else:
        raise NotImplementedError
    for limit in limits:
        if limit.is_exceeded(kwargs.get("count", 1), kwargs.get("instance")):
            raise lib.LimitReached(limit)


@receiver(signals.post_save, sender=core_models.User)
def create_user_limits(sender, instance, **kwargs):
    """Create limits for new user."""
    if not kwargs.get("created"):
        return
    request = lib_signals.get_request()
    creator = request.user if request else None
    global_params = dict(param_tools.get_global_parameters("limits"))
    for name, definition in utils.get_user_limit_templates():
        ct = ContentType.objects.get_by_natural_key(
            *definition["content_type"].split(".")
        )
        max_value = 0
        # creator can be None if user was created by a factory
        if not creator or creator.is_superuser:
            max_value = global_params[f"deflt_user_{name}_limit"]
        models.UserObjectLimit.objects.create(
            user=instance, name=name, content_type=ct, max_value=max_value
        )


@receiver(signals.post_save, sender=admin_models.Domain)
def create_domain_limits(sender, instance, **kwargs):
    """Create limits for new domain."""
    if not kwargs.get("created"):
        return
    global_params = dict(param_tools.get_global_parameters("limits"))
    for name, _definition in utils.get_domain_limit_templates():
        max_value = global_params[f"deflt_domain_{name}_limit"]
        models.DomainObjectLimit.objects.create(
            domain=instance, name=name, max_value=max_value
        )


@receiver(core_signals.account_deleted)
def move_resource(sender, user, **kwargs):
    """Move remaining resource to another user."""
    owner = permissions.get_object_owner(user)
    if owner.is_superuser or owner.role != "Resellers":
        return
    utils.move_pool_resource(owner, user)


@receiver(core_signals.user_can_set_role)
def user_can_set_role(sender, user, role, account=None, **kwargs):
    """Check if the user can still set this role.

    The only interesting case concerns resellers defining new domain
    administrators. We want to check if they are allowed to do this
    operation before any modification is made to :keyword:`account`.

    :param ``User`` user: connected user
    :param str role: role to check
    :param ``User`` account: account modified (None on creation)
    """
    condition = (
        not param_tools.get_global_parameter("enable_admin_limits")
        or role != "DomainAdmins"
    )
    if condition:
        return True
    lname = "domain_admins"
    condition = (
        user.is_superuser or not user.userobjectlimit_set.get(name=lname).is_exceeded()
    )
    if condition:
        return True
    if account is not None and account.role == role:
        return True
    return False


@receiver(core_signals.account_role_changed)
def move_pool_resource(sender, account, role, **kwargs):
    """Move remaining resource to owner if needed."""
    owner = permissions.get_object_owner(account)
    if not owner or owner.is_superuser or owner.role != "Resellers":
        # Domain admins can't change the role so nothing to check.
        return

    if role not in ["DomainAdmins", "Resellers"]:
        utils.move_pool_resource(owner, account)
