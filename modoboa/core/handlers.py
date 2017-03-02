"""Modoboa core signal handlers."""

import logging

from django.core.urlresolvers import reverse
from django.db.models import signals
from django.dispatch import receiver
from django.utils.translation import ugettext as _

from django.contrib.sites import models as sites_models

from reversion import revisions as reversion

from modoboa.lib import exceptions
from modoboa.lib import permissions
from modoboa.lib.signals import get_request

from . import models
from . import signals as core_signals
from . import utils


@receiver(reversion.post_revision_commit)
def post_revision_commit(sender, **kwargs):
    """Custom post-revision hook.

    We want to track all creations and modifications of admin. objects
    (alias, mailbox, user, domain, domain alias, etc.) so we use
    django-reversion for that.

    """
    from modoboa.lib.signals import get_request

    current_user = get_request().user.username
    logger = logging.getLogger("modoboa.admin")
    for version in kwargs["versions"]:
        if version.object is None:
            continue
        prev_revisions = reversion.get_for_object(version.object)
        if prev_revisions.count() == 1:
            action = _("added")
            level = "info"
        else:
            action = _("modified")
            level = "warning"
        message = _("%(object)s '%(name)s' %(action)s by user %(user)s") % {
            "object": unicode(version.content_type).capitalize(),
            "name": version.object_repr, "action": action,
            "user": current_user
        }
        getattr(logger, level)(message)


@receiver(signals.post_delete)
def log_object_removal(sender, instance, **kwargs):
    """Custom post-delete hook.

    We want to know who was responsible for an object deletion.
    """
    from reversion.models import Version

    if not reversion.is_registered(sender):
        return
    del_list = reversion.get_deleted(sender)
    try:
        version = del_list.get(object_id=instance.id)
    except Version.DoesNotExist:
        return
    logger = logging.getLogger("modoboa.admin")
    msg = _("%(object)s '%(name)s' %(action)s by user %(user)s") % {
        "object": unicode(version.content_type).capitalize(),
        "name": version.object_repr, "action": _("deleted"),
        "user": get_request().user.username
    }
    logger.critical(msg)


def create_local_config(sender, **kwargs):
    """Create local config if needed."""
    using = kwargs.get("using")
    if using != "default":
        return
    if models.LocalConfig.objects.using(kwargs["using"]).exists():
        return
    models.LocalConfig.objects.create(
        site=sites_models.Site.objects.get_current())


@receiver(signals.pre_delete, sender=models.User)
def update_permissions(sender, instance, **kwargs):
    """Permissions cleanup."""
    from_user = get_request().user
    if from_user == instance:
        raise exceptions.PermDeniedException(
            _("You can't delete your own account")
        )

    if not from_user.can_access(instance):
        raise exceptions.PermDeniedException

    # We send an additional signal before permissions are removed
    core_signals.account_deleted.send(
        sender="update_permissions", user=instance)
    owner = permissions.get_object_owner(instance)
    if owner == instance:
        # The default admin is being removed...
        owner = from_user
    # Change ownership of existing objects
    for ooentry in instance.objectaccess_set.filter(is_owner=True):
        if ooentry.content_object is not None:
            permissions.grant_access_to_object(
                owner, ooentry.content_object, True)
            permissions.ungrant_access_to_object(
                ooentry.content_object, instance)
    # Remove existing permissions on this user
    permissions.ungrant_access_to_object(instance)


@receiver(core_signals.get_top_notifications)
def check_for_new_versions(sender, include_all, **kwargs):
    """Check if new versions are available."""
    request = get_request()
    if not request.user.is_superuser:
        return []
    status, extensions = utils.check_for_updates(request)
    if not status:
        return [{"id": "newversionavailable"}] if include_all else []
    return [{
        "id": "newversionavailable",
        "url": reverse("core:index") + "#info/",
        "text": _("One or more updates are available"),
        "level": "info",
    }]
