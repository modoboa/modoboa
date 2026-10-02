"""Custom test runner."""

import multiprocessing

from django.apps import apps
from django.conf import settings
from django.test import runner

# Used when the settings don't name one
DEFAULT_REDIS_TEST_DB = 15

# Django supports neither forkserver (the default start method on Linux
# since Python 3.14) nor spawn for what this runner sets up: workers must
# inherit the test environment of the main process.
multiprocessing.set_start_method("fork", force=True)


def setup_test_redis(db):
    """Point Redis and the RQ queues to the given database.

    The workers of a development stack listen on the same queues as the
    tests: without this, a worker picks up the jobs a test enqueues, and
    the test then runs its own worker on an empty queue and fails.
    """
    settings.REDIS_QUOTA_DB = db
    settings.REDIS_URL = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{db}"
    # django_rq reads RQ_QUEUES on every access, so updating it here is
    # enough for the queues the tests will create.
    for queue in getattr(settings, "RQ_QUEUES", {}).values():
        queue["URL"] = settings.REDIS_URL


def get_redis_test_db():
    return getattr(settings, "REDIS_TEST_DB", DEFAULT_REDIS_TEST_DB)


def _init_worker(*args, **kwargs):
    """Prepare a worker of the parallel test runner.

    Each worker gets a Redis database of its own, below the one of the
    main process, so that workers never share their queues.
    """
    runner._init_worker(*args, **kwargs)
    setup_test_redis(get_redis_test_db() - runner._worker_id)
    # Workers are daemonic, and multiprocessing forbids daemonic
    # processes to have children: some tests start their own (policy
    # daemon for example).
    multiprocessing.current_process().daemon = False


def group_subsuites(subsuites):
    """Run test cases sharing an external resource in the same worker.

    Test cases declare the resource with a ``parallel_group``
    attribute (an LDAP directory, for example): running them
    concurrently would make them interfere.
    """
    result = []
    groups = {}
    for subsuite in subsuites:
        group = getattr(next(iter(subsuite)), "parallel_group", None)
        if group is None:
            result.append(subsuite)
        elif group in groups:
            groups[group].addTests(subsuite)
        else:
            groups[group] = subsuite
            result.append(subsuite)
    return result


class ParallelTestSuite(runner.ParallelTestSuite):
    init_worker = _init_worker

    def __init__(self, subsuites, *args, **kwargs):
        super().__init__(group_subsuites(subsuites), *args, **kwargs)


class CustomTestRunner(runner.DiscoverRunner):
    """Test runner preparing the environment the suite expects.

    It makes all the unmanaged models of the project managed for the
    duration of the run (many thanks to the Caktus Group:
    http://bit.ly/1N8TcHW), and moves Redis to a database of its own so
    that the tests never share their queues with a running development
    stack.
    """

    parallel_test_suite = ParallelTestSuite
    unmanaged_models = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Workers use the Redis databases below the one of the main
        # process, database 0 is left to the development stack.
        max_processes = get_redis_test_db() - 1
        if self.parallel > max_processes:
            self.log(
                f"Limiting test processes to {max_processes} "
                "(one Redis database each)."
            )
            self.parallel = max_processes

    def setup_test_environment(self, *args, **kwargs):
        """Mark amavis models as managed during testing
        During database setup migrations are only run for managed models"""
        for m in apps.get_models():
            if m._meta.app_label == "amavis":
                self.unmanaged_models.append(m)
                m._meta.managed = True
        setup_test_redis(get_redis_test_db())
        super().setup_test_environment(*args, **kwargs)

    def teardown_test_environment(self, *args, **kwargs):
        """Revert modoboa_amavis models to unmanaged"""
        super().teardown_test_environment(*args, **kwargs)
        for m in self.unmanaged_models:
            m._meta.managed = False
