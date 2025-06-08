"""API v2 tests."""

from dateutil.relativedelta import relativedelta

from django.urls import reverse
from django.utils import timezone

from modoboa.core import models as core_models
from modoboa.admin import factories as admin_factories, models
from modoboa.lib.tests import ModoAPITestCase
from modoboa.maillog import factories


class StatisticsViewSetTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        admin_factories.populate_database()

    def test_list(self):
        url = reverse("v2:statistics-list")
        resp = self.client.get(url + "?gset=mailtraffic&period=day")
        self.assertEqual(resp.status_code, 200)

        self.set_global_parameter("greylist", True)
        resp = self.client.get(url + "?gset=mailtraffic&period=day")
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(url + "?gset=mailtraffic&period=custom&start=2021-05-01")
        self.assertEqual(resp.status_code, 400)

        resp = self.client.get(
            url + "?gset=mailtraffic&period=custom&start=2021-05-01&end=2021-05-02"
        )
        self.assertEqual(resp.status_code, 200)

    def test_list_as_domain_admin(self):
        account = core_models.User.objects.get(username="admin@test.com")
        self.authenticate_user(account)
        url = reverse("v2:statistics-list")
        resp = self.client.get(
            url + "?gset=mailtraffic&period=day&searchquery=test.com"
        )
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(url + "?gset=mailtraffic&period=day")
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(
            url + "?gset=mailtraffic&period=day&searchquery=test2.com"
        )
        self.assertEqual(resp.status_code, 403)


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
