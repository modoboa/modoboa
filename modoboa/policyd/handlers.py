"""App related signal handlers."""

from django.db.models import signals
from django.dispatch import receiver

from modoboa.admin import models as admin_models
from modoboa.lib.redis import get_redis_connection

from . import constants

# Move a counter to a new key, keeping its current value.
RENAME_COUNTER_SCRIPT = """
local value = redis.call('HGET', KEYS[1], ARGV[1])
if value then
  redis.call('HSET', KEYS[1], ARGV[2], value)
  redis.call('HDEL', KEYS[1], ARGV[1])
end
return value
"""


def rename_counter(rclient, old_key, new_key):
    """Move counter stored under old_key to new_key."""
    rclient.eval(RENAME_COUNTER_SCRIPT, 1, constants.REDIS_HASHNAME, old_key, new_key)


def set_message_limit(instance, old_key, key):
    """Store message limit in Redis.

    The applied limit and key are remembered on the instance so that
    saving it several times doesn't apply the same change twice.
    """
    old_message_limit = instance._loaded_values.get("message_limit")
    key_changed = bool(old_key) and old_key != key
    instance._loaded_values["message_limit"] = instance.message_limit
    instance._policyd_counter_key = key
    if old_message_limit is None and instance.message_limit is None:
        return
    if old_message_limit == instance.message_limit and not key_changed:
        return
    rclient = get_redis_connection()
    if key_changed:
        rename_counter(rclient, old_key, key)
    if instance.message_limit is None:
        rclient.hdel(constants.REDIS_HASHNAME, key)
        return
    if old_message_limit is None or not rclient.hexists(constants.REDIS_HASHNAME, key):
        rclient.hset(constants.REDIS_HASHNAME, key, instance.message_limit)
        return
    diff = instance.message_limit - old_message_limit
    if diff:
        rclient.hincrby(constants.REDIS_HASHNAME, key, diff)


def has_message_limit(instance):
    """Check if a counter may exist for instance."""
    return (
        instance.message_limit is not None
        or instance._loaded_values.get("message_limit") is not None
    )


def get_domain_counter_key(instance):
    """Return the key under which the domain counter is currently stored."""
    return getattr(instance, "_policyd_counter_key", instance.oldname)


def get_mailbox_counter_key(instance):
    """Return the key under which the mailbox counter is currently stored."""
    return getattr(instance, "_policyd_counter_key", instance.old_full_address)


@receiver(signals.post_save, sender=admin_models.Domain)
def set_domain_message_limit(sender, instance, created, **kwargs):
    """Store domain message limit in Redis."""
    old_key = get_domain_counter_key(instance)
    set_message_limit(instance, old_key, instance.name)
    if created or not old_key or old_key == instance.name:
        return
    # Domain has been renamed: move mailbox counters too
    rclient = get_redis_connection()
    for mb in instance.mailbox_set.filter(message_limit__isnull=False):
        rename_counter(rclient, f"{mb.address}@{old_key}", mb.full_address)


@receiver(signals.post_save, sender=admin_models.Mailbox)
def set_mailbox_message_limit(sender, instance, created, **kwargs):
    """Store mailbox message limit in Redis."""
    set_message_limit(
        instance, get_mailbox_counter_key(instance), instance.full_address
    )


@receiver(signals.post_delete, sender=admin_models.Domain)
def delete_domain_message_counter(sender, instance, **kwargs):
    """Remove domain counter from Redis."""
    if not has_message_limit(instance):
        return
    get_redis_connection().hdel(
        constants.REDIS_HASHNAME, get_domain_counter_key(instance)
    )


@receiver(signals.post_delete, sender=admin_models.Mailbox)
def delete_mailbox_message_counter(sender, instance, **kwargs):
    """Remove mailbox counter from Redis."""
    if not has_message_limit(instance):
        return
    get_redis_connection().hdel(
        constants.REDIS_HASHNAME, get_mailbox_counter_key(instance)
    )
