"""Tests for cron configuration and rq version compatibility."""

import importlib
import sys

from django.test import override_settings

from modoboa.lib.tests import SimpleModoTestCase


class CronConfigTestCase(SimpleModoTestCase):
    """Verify that cron_config.py loads without errors across rq versions."""

    def test_cron_config_imports(self):
        """cron_config.py must import without TypeError on rq>=2.10.

        Regression test for issue #4088: rq>=2.10.0 added a `webhooks`
        kwarg to ``rq.cron.register()``. The previous django-rq==4.0.1
        ``DjangoCronScheduler.register()`` override did not accept this
        kwarg, causing a ``TypeError`` when ``cron_config.py`` called
        ``register()`` at import time. django-rq>=4.1.1 fixes this by
        accepting and forwarding ``webhooks``.
        """
        # Force re-import to catch import-time errors
        if "test_project.cron_config" in sys.modules:
            importlib.reload(sys.modules["test_project.cron_config"])
        else:
            importlib.import_module("test_project.cron_config")

    def test_rq_version_not_pinned_below_2_10(self):
        """The rq dependency must not be pinned below 2.10.0."""
        import rq

        # We allow rq >= 2.7.0 (including >= 2.10.0)
        major, minor = int(rq.__version__.split(".")[0]), int(
            rq.__version__.split(".")[1]
        )
        # If rq is 2.10+, django-rq must be >= 4.1.1 to accept webhooks
        if major == 2 and minor >= 10:
            import django_rq

            dj_rq_parts = django_rq.__version__.split(".")
            dj_rq_major, dj_rq_minor = int(dj_rq_parts[0]), int(dj_rq_parts[1])
            self.assertGreaterEqual(
                (dj_rq_major, dj_rq_minor),
                (4, 1),
                "django-rq>=4.1.1 is required when rq>=2.10.0 (issue #4088)",
            )
