"""API v2 tests."""

from dateutil.relativedelta import relativedelta

from django.urls import reverse
from django.utils import timezone

from modoboa.admin import factories as admin_factories, models
from modoboa.lib.tests import ModoAPITestCase
from modoboa.maillog import factories


class StatisticsViewSetTestCase(ModoAPITestCase):

    def test_list(self):
        url = reverse("v2:statistics-list")
        resp = self.client.get(url + "?gset=mailtraffic&period=day")
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(url + "?gset=mailtraffic&period=custom&start=2021-05-01")
        self.assertEqual(resp.status_code, 400)

        resp = self.client.get(
            url + "?gset=mailtraffic&period=custom&start=2021-05-01&end=2021-05-02"
        )
        self.assertEqual(resp.status_code, 200)


class MaillogViewSetTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        admin_factories.populate_database()
        domain = models.Domain.objects.get(name="test.com")
        factories.MaillogFactory(from_domain=domain)
        factories.MaillogFactory(
            to_domain=domain,
            status="received",
            date=timezone.now() + relativedelta(days=1),
        )
        factories.MaillogFactory(date=timezone.now() + relativedelta(days=2))
        factories.MaillogFactory(date=timezone.now() + relativedelta(days=3))

    def test_list(self):
        url = reverse("v2:maillog-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 4)
