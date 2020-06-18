"""App related signal handlers."""

import redis

from django.conf import settings
from django.db.models import signals
from django.dispatch import receiver

from modoboa.admin import models as admin_models

from . import constants


def set_message_limit(instance, key):
    """Store message limit in Redis."""
    old_message_limit = instance._loaded_values.get("message_limit")
    if old_message_limit == instance.message_limit:
        return
    rclient = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_QUOTA_DB
    )
    if instance.message_limit is None:
        # delete existing key
        if rclient.hexists(constants.REDIS_HASHNAME, key):
            rclient.hdel(constants.REDIS_HASHNAME, key)
        return
    if old_message_limit is not None:
        diff = instance.message_limit - old_message_limit
    else:
        diff = instance.message_limit
    rclient.hincrby(constants.REDIS_HASHNAME, key, diff)


@receiver(signals.post_save, sender=admin_models.Domain)
def set_domain_message_limit(sender, instance, created, **kwargs):
    """Store domain message limit in Redis."""
    set_message_limit(instance, instance.name)


@receiver(signals.post_save, sender=admin_models.Mailbox)
def set_mailbox_message_limit(sender, instance, created, **kwargs):
    """Store mailbox message limit in Redis."""
    set_message_limit(instance, instance.full_address)
