from django.urls import reverse
from django.utils import timezone

from dateutil.relativedelta import relativedelta

from modoboa.admin import factories as admin_factories
from modoboa.core.models import User
from modoboa.lib.tests import ModoAPITestCase
from modoboa.postfix_autoreply import factories, models


class ARMessageViewSetTestCase(ModoAPITestCase):
    """API test case."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        admin_factories.populate_database()
        cls.account = User.objects.get(username="user@test.com")
        cls.account2 = User.objects.get(username="user@test2.com")
        cls.arm = factories.ARmessageFactory(mbox=cls.account.mailbox)
        cls.arm2 = factories.ARmessageFactory(mbox=cls.account2.mailbox)

    def test_retrieve_armessage(self):
        url = reverse("api:armessage-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        # Test filters
        response = self.client.get(url + f"?mbox={self.account.mailbox.full_address}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        response = self.client.get(url + f"?mbox={self.account.mailbox.address}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        response = self.client.get(url + f"?mbox__user={self.account.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        # Test retrieve
        url = reverse("api:armessage-detail", args=[response.data[0]["id"]])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_retrieve_armessage_domadmin(self):
        admin = User.objects.get(username="admin@test.com")
        self.client.logout()
        self.client.force_login(admin)
        url = reverse("api:armessage-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        url = reverse("api:armessage-detail", args=[self.arm2.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_retrieve_armessage_simpleuser(self):
        self.client.logout()
        self.client.force_login(self.account)
        url = reverse("api:armessage-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        url = reverse("api:armessage-detail", args=[self.arm2.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_create_armessage(self):
        url = reverse("api:armessage-list")
        account = User.objects.get(username="user@test2.com")
        data = {
            "mbox": account.mailbox.pk,
            "subject": "Je suis absent",
            "content": "Je reviens bientôt",
            "enabled": True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)

    def test_update_armessage(self):
        url = reverse("api:armessage-detail", args=[self.arm.pk])
        data = {"enabled": False}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 200)
        self.arm.refresh_from_db()
        self.assertFalse(self.arm.enabled)

        data = {
            "mbox": self.account.mailbox.pk,
            "subject": "Je suis absent",
            "content": "Je reviens bientôt",
            "enabled": True,
            "untildate": (timezone.now() + relativedelta(days=1)).isoformat(),
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 200)
        self.arm.refresh_from_db()
        self.assertIsNot(self.arm.untildate, None)

    def test_date_constraints(self):
        url = reverse("api:armessage-detail", args=[self.arm.pk])
        data = {
            "mbox": self.account.mailbox.pk,
            "subject": "Je suis absent",
            "content": "Je reviens bientôt",
            "enabled": True,
            "untildate": timezone.now().isoformat(),
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["untildate"][0], "This date is over")

        data.update(
            {
                "fromdate": (timezone.now() + relativedelta(days=2)).isoformat(),
                "untildate": (timezone.now() + relativedelta(days=1)).isoformat(),
            }
        )
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["untildate"][0], "Must be greater than start date"
        )


class AccountARMessageViewSetTestCase(ModoAPITestCase):
    """API test case."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        admin_factories.populate_database()
        cls.account = User.objects.get(username="user@test.com")

    def test_get_armessage(self):
        url = reverse("api:account_armessage-armessage")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.client.logout()
        self.client.force_login(self.account)
        self.assertFalse(
            models.ARmessage.objects.filter(mbox=self.account.mailbox).exists()
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            models.ARmessage.objects.filter(mbox=self.account.mailbox).exists()
        )

    def test_set_armessage(self):
        self.client.logout()
        self.client.force_login(self.account)
        url = reverse("api:account_armessage-armessage")
        fromdate = timezone.now()
        todate = fromdate + relativedelta(days=4)
        data = {
            "enabled": True,
            "subject": "Je suis absent",
            "content": "Je reviendrai",
            "fromdate": fromdate.isoformat(),
            "untildate": todate.isoformat(),
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        armessage = models.ARmessage.objects.get(mbox=self.account.mailbox)
        self.assertTrue(armessage.enabled)
