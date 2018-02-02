# -*- coding: utf-8 -*-

"""Modoboa core signal handlers."""

from __future__ import unicode_literals

import logging

from reversion import revisions as reversion
from reversion.models import Version

from django.contrib.sites import models as sites_models
from django.db.models import signals
from django.dispatch import receiver
from django.urls import reverse
from django.utils.encoding import smart_text
from django.utils.translation import ugettext as _

from modoboa.lib import exceptions, permissions
from modoboa.lib.signals import get_request
from . import models, signals as core_signals, utils


@receiver(reversion.post_revision_commit)
def post_revision_commit(sender, **kwargs):
    """Custom post-revision hook.

    We want to track all creations and modifications of admin. objects
    (alias, mailbox, user, domain, domain alias, etc.) so we use
    django-reversion for that.

    """
    current_user = get_request().user.username
    logger = logging.getLogger("modoboa.admin")
    for version in kwargs["versions"]:
        if version.object is None:
            continue
        prev_revisions = Version.objects.get_for_object(version.object)
        if prev_revisions.count() == 1:
            action = _("added")
            level = "info"
        else:
            action = _("modified")
            level = "warning"
        message = _("%(object)s '%(name)s' %(action)s by user %(user)s") % {
            "object": smart_text(version.content_type).capitalize(),
            "name": version.object_repr, "action": action,
            "user": current_user
        }
        getattr(logger, level)(message)


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
        "object": smart_text(version.content_type).capitalize(),
        "name": version.object_repr, "action": _("deleted")
    }
    request = get_request()
    if request:
        msg += _("user {}").format(request.user.username)
    else:
        msg += _("management command")
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
    request = get_request()
    # request migth be None (management command context)
    if request:
        from_user = request.user
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
