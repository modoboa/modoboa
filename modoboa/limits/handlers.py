"""Django signal handlers for limits."""

from django.db.models import signals
from django.dispatch import receiver

from django.contrib.contenttypes.models import ContentType

from modoboa.core import models as core_models
from modoboa.core import signals as core_signals
from modoboa.lib import signals as lib_signals
from modoboa.lib import parameters

from . import lib
from . import models
from . import utils


@receiver(core_signals.can_create_object)
def check_object_limit(sender, user, object_type, **kwargs):
    """Check if user can create a new object."""
    if user.is_superuser:
        return True
    limit = user.objectlimit_set.get(name=object_type)
    count = kwargs.get("count", 1)
    if limit.is_exceeded(count):
        raise lib.LimitReached(limit)


@receiver(signals.post_save, sender=core_models.User)
def create_user_limits(sender, instance, **kwargs):
    """Create limits for new user."""
    if not kwargs.get("created"):
        return
    request = lib_signals.get_request()
    creator = request.user if request else None
    for name, definition in utils.get_limit_templates():
        ct = ContentType.objects.get_by_natural_key(
            *definition["content_type"].split("."))
        max_value = 0
        if not creator or creator.is_superuser:
            max_value = int(
                parameters.get_admin("DEFLT_{}_LIMIT".format(name.upper())))
        models.ObjectLimit.objects.create(
            user=instance, name=name, content_type=ct, max_value=max_value)
