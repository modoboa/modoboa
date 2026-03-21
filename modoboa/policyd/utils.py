"""Tooling."""

from modoboa.lib.redis import get_redis_connection

from . import constants


def get_message_counter(key):
    """Return current counter for given key."""
    rclient = get_redis_connection(hget_return_type=None)
    value = rclient.hget(constants.REDIS_HASHNAME, key)
    if value is None:
        return None
    return int(value)
