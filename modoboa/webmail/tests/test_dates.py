"""Tests for the dates displayed in the messages list."""

import datetime
from unittest import mock

from django.test import SimpleTestCase, override_settings
from django.utils import timezone, translation

from modoboa.webmail.lib import imapheader

NOW = datetime.datetime(2026, 9, 15, 22, 30, tzinfo=datetime.timezone.utc)


@override_settings(TIME_ZONE="Europe/Paris", USE_TZ=True)
@mock.patch("django.utils.timezone.now", return_value=NOW)
@mock.patch("modoboa.webmail.lib.imapheader.get_request")
class DatesTestCase(SimpleTestCase):
    def setUp(self):
        super().setUp()
        timezone.deactivate()

    def _setup_request(self, get_request):
        get_request.return_value.user.language = "fr"

    def test_date_in_current_time_zone(self, get_request, now):
        self._setup_request(get_request)
        # 22:00 in New York is 04:00 the next day in Paris
        result = imapheader.parse_date("Mon, 14 Sep 2026 22:00:00 -0400")
        self.assertIn("04:00", result)

    def test_today_shows_the_time_only(self, get_request, now):
        self._setup_request(get_request)
        # 23:00 UTC is already the current day in Paris (01:00, Sept. 16th)
        result = imapheader.parse_date("Tue, 15 Sep 2026 23:00:00 +0000")
        self.assertEqual(result, "01:00")

    def test_this_week_shows_the_weekday(self, get_request, now):
        self._setup_request(get_request)
        result = imapheader.parse_date("Sat, 12 Sep 2026 10:00:00 +0000")
        # The weekday name follows the active locale, English here
        self.assertEqual(result, "Sat 12:00")

    def test_this_year_shows_the_day_and_month(self, get_request, now):
        self._setup_request(get_request)
        # Two weeks old: neither the time nor the year tells it apart
        result = imapheader.parse_date("Tue, 1 Sep 2026 10:00:00 +0000")
        self.assertNotIn("2026", result)
        self.assertNotIn("12:00", result)
        self.assertIn("1", result)

    def test_another_year_shows_the_year(self, get_request, now):
        self._setup_request(get_request)
        result = imapheader.parse_date("Fri, 1 Sep 2025 10:00:00 +0000")
        self.assertIn("2025", result)

    def test_invalid_date_is_returned_as_is(self, get_request, now):
        self._setup_request(get_request)
        self.assertEqual(imapheader.parse_date("not a date"), "not a date")

    def test_scheduled_today_shows_time_only(self, get_request, now):
        self._setup_request(get_request)
        # 23:00 UTC is already tomorrow in Paris (01:00, Sept. 16th)...
        result = imapheader.parse_scheduled_datetime("2026-09-15T23:00:00+00:00")
        self.assertEqual(result, "01:00")

    def test_scheduled_same_day_number_other_month(self, get_request, now):
        self._setup_request(get_request)
        # Same day number (16), another month: the full date is needed
        result = imapheader.parse_scheduled_datetime("2026-10-16T08:00:00+00:00")
        self.assertIn("2026", result)
        self.assertIn("10:00", result)

    def test_full_date(self, get_request, now):
        self._setup_request(get_request)
        with translation.override("fr"):
            result = imapheader.format_full_date("Tue, 1 Sep 2026 10:00:00 +0000")
        self.assertEqual(result, "1 septembre 2026 12:00")

    def test_full_date_not_a_date(self, get_request, now):
        self.assertEqual(imapheader.format_full_date("not a date"), "not a date")
