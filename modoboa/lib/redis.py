import functools

import redis

from django.conf import settings


@functools.cache
def _get_connection_pool(url, sentinels, master, db) -> redis.ConnectionPool:
    """Return a connection pool shared by all clients of this process.

    Pools are keyed by connection settings so a settings change (in
    tests for example) gives a new pool.
    """
    if sentinels is None:
        return redis.ConnectionPool.from_url(url)
    sentinel = redis.sentinel.Sentinel(list(sentinels), socket_timeout=0.1, db=db)
    return sentinel.master_for(master, socket_timeout=0.1).connection_pool


def get_redis_connection(hget_return_type=int) -> redis.Redis:
    """Return a client connection to Redis server."""
    if not getattr(settings, "REDIS_SENTINEL", False):
        pool = _get_connection_pool(settings.REDIS_URL, None, None, None)
    else:
        pool = _get_connection_pool(
            None,
            tuple(tuple(sentinel) for sentinel in settings.REDIS_SENTINELS),
            settings.REDIS_MASTER,
            settings.REDIS_QUOTA_DB,
        )
    rclient = redis.Redis(connection_pool=pool)
    if hget_return_type:
        rclient.set_response_callback("HGET", hget_return_type)
    return rclient
