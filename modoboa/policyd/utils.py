"""Tooling."""

import redis

from django.conf import settings

from . import constants


def get_redis_connection():
    """Return a client connection to Redis server."""
    rclient = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_QUOTA_DB
    )
    rclient.set_response_callback("HGET", int)
    return rclient


def get_message_counter(key):
    """Return current counter for given key."""
    rclient = get_redis_connection()
    return rclient.hget(constants.REDIS_HASHNAME, key)
