"""Modoboa core signal handlers."""

import logging

from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import ugettext as _

from django.contrib.sites import models as sites_models

from reversion import revisions as reversion

from . import models


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


@receiver(post_delete)
def log_object_removal(sender, instance, **kwargs):
    """Custom post-delete hook.

    We want to know who was responsible for an object deletion.
    """
    from reversion.models import Version
    from modoboa.lib.signals import get_request

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
    if models.LocalConfig.objects.using(kwargs["using"]).exists():
        return
    models.LocalConfig.objects.create(
        site=sites_models.Site.objects.get_current())
