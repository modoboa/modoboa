from django.test import SimpleTestCase
from django.test.utils import override_settings

from ..checks import settings_checks


class CheckSessionCookieSecureTest(SimpleTestCase):
    @override_settings(USE_TZ=False)
    def test_use_tz_false(self):
        """If USE_TZ is off provide one warning."""
        self.assertEqual(
            settings_checks.check_use_tz_enabled(None),
            [settings_checks.W001]
        )

    @override_settings(USE_TZ=True)
    def test_use_tz_true(self):
        """If USE_TZ is on, there's no warning about it."""
        self.assertEqual(settings_checks.check_use_tz_enabled(None), [])
