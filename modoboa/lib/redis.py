import redis

from django.conf import settings


def get_redis_connection(hget_return_type=int) -> redis.Redis:
    """Return a client connection to Redis server."""
    if not getattr(settings, "REDIS_SENTINEL", False):
        rclient = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_QUOTA_DB,
        )
    else:
        sentinel = redis.sentinel.Sentinel(
            settings.REDIS_SENTINELS, socket_timeout=0.1, db=settings.REDIS_QUOTA_DB
        )
        rclient = sentinel.master_for(settings.REDIS_MASTER, socket_timeout=0.1)
    if hget_return_type:
        rclient.set_response_callback("HGET", hget_return_type)
    return rclient
