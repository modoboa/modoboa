"""Tests for cron configuration and rq version compatibility."""

import importlib
import sys

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
        from packaging.version import parse

        import rq

        rq_ver = parse(rq.__version__)
        # If rq is 2.10+, django-rq must be >= 4.1.1 to accept webhooks
        if rq_ver >= parse("2.10.0"):
            import django_rq

            dj_rq_ver = parse(django_rq.__version__)
            self.assertGreaterEqual(
                dj_rq_ver,
                parse("4.1.1"),
                "django-rq>=4.1.1 is required when rq>=2.10.0 (issue #4088)",
            )
