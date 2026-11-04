"""Modoboa core signal handlers."""

import logging

from reversion import revisions as reversion
from reversion.models import Version

from django.contrib.sites import models as sites_models
from django.db.models import signals
from django.dispatch import receiver
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from modoboa.core.utils import check_for_deprecated_password_schemes
from modoboa.lib import exceptions, permissions
from modoboa.lib.signals import get_request
from . import models, signals as core_signals, utils
from .loggers import audit


def _action_code(version, verb: str) -> str:
    return f"{version.content_type.app_label}.{version.content_type.model}.{verb}"


@receiver(reversion.post_revision_commit)
def post_revision_commit(sender, **kwargs):
    """Custom post-revision hook.

    We want to track all creations and modifications of admin. objects
    (alias, mailbox, user, domain, domain alias, etc.) so we use
    django-reversion for that.

    """
    request = get_request()
    if request:
        template = _("%(object)s '%(name)s' %(action)s by user %(user)s")
    else:
        template = _("%(object)s '%(name)s' %(action)s by management command")
    logger = logging.getLogger("modoboa.admin")
    for version in kwargs["versions"]:
        if version.object is None:
            continue
        prev_revisions = Version.objects.get_for_object(version.object)
        if prev_revisions.count() == 1:
            action = _("added")
            level = "info"
            code = "created"
        else:
            action = _("modified")
            level = "warning"
            code = "modified"
        message = template % {
            "object": smart_str(version.content_type).capitalize(),
            "name": version.object_repr,
            "action": action,
            "user": request.user.username if request else "",
        }
        getattr(logger, level)(
            message,
            extra=audit(_action_code(version, code), request, obj=version.object),
        )


@receiver(signals.post_delete)
def log_object_removal(sender, instance, **kwargs):
    """Custom post-delete hook.

    We want to know who was responsible for an object deletion.
    """
    if not reversion.is_registered(sender):
        return
    del_list = Version.objects.get_deleted(sender)
    try:
        version = del_list.get(object_id=instance.id)
    except Version.DoesNotExist:
        return
    logger = logging.getLogger("modoboa.admin")
    msg = _("%(object)s '%(name)s' %(action)s by ") % {
        "object": smart_str(version.content_type).capitalize(),
        "name": version.object_repr,
        "action": _("deleted"),
    }
    request = get_request()
    if request:
        msg += _("user {}").format(request.user.username)
    else:
        msg += _("management command")
    logger.critical(
        msg, extra=audit(_action_code(version, "deleted"), request, obj=instance)
    )


def create_local_config(sender, **kwargs):
    """Create local config if needed."""
    using = kwargs.get("using")
    if using != "default":
        return
    if models.LocalConfig.objects.using(kwargs["using"]).exists():
        return
    models.LocalConfig.objects.create(site=sites_models.Site.objects.get_current())


@receiver(signals.pre_delete, sender=models.User)
def update_permissions(sender, instance, **kwargs):
    """Permissions cleanup."""
    request = get_request()
    # request migth be None (management command context)
    from_user = request.user if request else None
    if from_user is not None:
        if from_user == instance:
            raise exceptions.PermDeniedException(_("You can't delete your own account"))

        if not from_user.can_access(instance):
            raise exceptions.PermDeniedException

    # We send an additional signal before permissions are removed
    core_signals.account_deleted.send(sender="update_permissions", user=instance)
    # Change ownership of existing objects
    owner = permissions.get_object_owner(instance)
    if owner is None or owner == instance:
        # The default admin owns itself: fall back on the user asking for
        # the removal, then (inside transfer_ownership) on any other
        # active super admin.
        owner = from_user
    permissions.transfer_ownership(instance, owner)
    # Remove existing permissions on this user
    permissions.ungrant_access_to_object(instance)


@receiver(core_signals.get_top_notifications)
def check_for_new_versions(sender, include_all: bool, **kwargs) -> list:
    """Check if new versions are available."""
    request = get_request()
    if not request.user.is_superuser:
        return []
    result = []
    status, extensions = utils.check_for_updates()
    if status:
        result += [
            {
                "id": "newversionavailable",
                "text": _("One or more updates are available"),
                "color": "info",
                "url": "/admin/information",
                "target": "admin",
            }
        ]
    elif include_all:
        result += [{"id": "newversionavailable"}]
    hasher = check_for_deprecated_password_schemes()
    if hasher:
        result += [
            {
                "id": "deprecatedpasswordscheme",
                "text": _("You are still using a deprecated password scheme (%s)")
                % hasher.name,
                "color": "warning",
                "url": "/admin/information",
                "target": "admin",
            }
        ]
    return result
