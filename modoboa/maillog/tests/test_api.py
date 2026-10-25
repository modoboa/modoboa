"""Statistics API tests."""

from unittest import mock

from django.urls import reverse

from modoboa.admin import factories as admin_factories
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoAPITestCase
from modoboa.maillog import graphics


class StatisticsViewSetTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # noqa
        super().setUpTestData()
        admin_factories.populate_database()
        admin_factories.DomainFactory(name="test.com.br")
        cls.dadmin = core_models.User.objects.get(username="admin@test.com")

    def get_statistics(self, **params):
        return self.client.get(
            reverse("v2:statistics-list"), {"period": "day", **params}
        )

    @mock.patch.object(graphics.MailTraffic, "export", return_value={})
    def test_superadmin_global_view(self, export):
        response = self.get_statistics(gset="mailtraffic")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(export.call_args.args[0], "global")

    @mock.patch.object(graphics.MailTraffic, "export", return_value={})
    def test_domain_admin_own_domain(self, export):
        self.authenticate_user(self.dadmin)
        response = self.get_statistics(gset="mailtraffic", searchquery="test.com")
        self.assertEqual(response.status_code, 200)
        # Exact match: test.com.br must not make the lookup ambiguous
        self.assertEqual(export.call_args.args[0], "test.com")

    @mock.patch.object(graphics.MailTraffic, "export", return_value={})
    def test_domain_admin_global_view_falls_back_to_domain(self, export):
        self.authenticate_user(self.dadmin)
        response = self.get_statistics(gset="mailtraffic")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(export.call_args.args[0], "test.com")

    def test_domain_admin_other_domain(self):
        self.authenticate_user(self.dadmin)
        response = self.get_statistics(gset="mailtraffic", searchquery="test2.com")
        self.assertEqual(response.status_code, 403)

    def test_domain_admin_account_graphics(self):
        self.authenticate_user(self.dadmin)
        response = self.get_statistics(gset="accountgraphicset")
        self.assertEqual(response.status_code, 404)
