"""Custom test runner."""

from django.apps import apps
from django.conf import settings
from django.test.runner import DiscoverRunner

# Used when the settings don't name one
DEFAULT_REDIS_TEST_DB = 15


class CustomTestRunner(DiscoverRunner):
    """Test runner preparing the environment the suite expects.

    It makes all the unmanaged models of the project managed for the
    duration of the run (many thanks to the Caktus Group:
    http://bit.ly/1N8TcHW), and moves Redis to a database of its own so
    that the tests never share their queues with a running development
    stack.
    """

    unmanaged_models = []

    def setup_test_environment(self, *args, **kwargs):
        """Mark amavis models as managed during testing
        During database setup migrations are only run for managed models"""
        for m in apps.get_models():
            if m._meta.app_label == "amavis":
                self.unmanaged_models.append(m)
                m._meta.managed = True
        self.setup_test_redis()
        super().setup_test_environment(*args, **kwargs)

    def setup_test_redis(self):
        """Point Redis and the RQ queues to the test database.

        The workers of a development stack listen on the same queues as the
        tests: without this, a worker picks up the jobs a test enqueues, and
        the test then runs its own worker on an empty queue and fails.
        """
        db = getattr(settings, "REDIS_TEST_DB", DEFAULT_REDIS_TEST_DB)
        settings.REDIS_QUOTA_DB = db
        settings.REDIS_URL = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{db}"
        # django_rq reads RQ_QUEUES on every access, so updating it here is
        # enough for the queues the tests will create.
        for queue in getattr(settings, "RQ_QUEUES", {}).values():
            queue["URL"] = settings.REDIS_URL

    def teardown_test_environment(self, *args, **kwargs):
        """Revert modoboa_amavis models to unmanaged"""
        super().teardown_test_environment(*args, **kwargs)
        for m in self.unmanaged_models:
            m._meta.managed = False
