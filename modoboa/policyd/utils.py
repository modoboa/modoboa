"""Tooling."""

import redis

from django.conf import settings

from . import constants


def get_redis_connection():
    """Return a client connection to Redis server."""
    if not getattr(settings, "REDIS_SENTINEL", False):
        rclient = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_QUOTA_DB,
        )
    else:
        sentinel = redis.sentinel.Sentinel(settings.REDIS_SENTINELS, socket_timeout=0.1)
        rclient = sentinel.master_for(settings.REDIS_MASTER, socket_timeout=0.1)
    rclient.set_response_callback("HGET", int)
    return rclient


def get_message_counter(key):
    """Return current counter for given key."""
    rclient = get_redis_connection()
    return rclient.hget(constants.REDIS_HASHNAME, key)
