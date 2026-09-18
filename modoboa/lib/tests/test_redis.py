"""Redis helpers tests."""

from django.test import SimpleTestCase, override_settings

from modoboa.lib.redis import get_redis_connection


class RedisConnectionTestCase(SimpleTestCase):
    """Test Redis connection helper."""

    def test_connection_pool_is_shared(self):
        rclient1 = get_redis_connection()
        rclient2 = get_redis_connection(bytes)
        self.assertIs(rclient1.connection_pool, rclient2.connection_pool)

    def test_response_callbacks_are_per_client(self):
        rclient1 = get_redis_connection()
        rclient2 = get_redis_connection(hget_return_type=None)
        rclient1.hset("modoboa_test_hash", "key", 12)
        try:
            self.assertEqual(rclient1.hget("modoboa_test_hash", "key"), 12)
            self.assertEqual(rclient2.hget("modoboa_test_hash", "key"), b"12")
        finally:
            rclient1.delete("modoboa_test_hash")

    def test_new_pool_when_settings_change(self):
        pool = get_redis_connection().connection_pool
        with override_settings(REDIS_URL="redis://localhost:6379/14"):
            other_pool = get_redis_connection().connection_pool
        self.assertIsNot(pool, other_pool)
        self.assertEqual(other_pool.connection_kwargs["db"], 14)
