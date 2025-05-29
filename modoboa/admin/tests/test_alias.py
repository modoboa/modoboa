"""Admin test cases."""

from django.urls import reverse

from modoboa.core.models import User
from modoboa.lib.tests import ModoAPITestCase
from .. import factories
from ..models import Alias, AliasRecipient


class AliasTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def test_alias_with_duplicated_recipient(self):
        """Check for duplicates."""
        values = {
            "address": "badalias@test.com",
            "recipients": ["user@test.com", "user@test.com"],
            "enabled": True,
        }
        response = self.client.post(reverse("v2:alias-list"), values, format="json")
        self.assertEqual(response.status_code, 201)
        alias = Alias.objects.get(address="badalias@test.com")
        self.assertEqual(alias.recipients_count, 1)

    def test_upper_case_alias(self):
        """Try to create an upper case alias."""
        user = User.objects.get(username="user@test.com")
        values = {
            "address": "Toto@test.com",
            "recipients": ["user@test.com"],
            "enabled": True,
        }
        response = self.client.post(reverse("v2:alias-list"), values, format="json")
        self.assertEqual(response.status_code, 201)
        mb = user.mailbox
        self.assertEqual(
            AliasRecipient.objects.filter(alias__internal=False, r_mailbox=mb).count(),
            2,
        )
        self.assertTrue(
            AliasRecipient.objects.filter(
                alias__internal=False, r_mailbox=mb, alias__address="toto@test.com"
            ).exists()
        )

    def test_append_alias_with_tag(self):
        """Try to create a alias with tag in recipient address"""
        values = {
            "address": "foobar@test.com",
            "recipients": ["user+spam@test.com"],
            "enabled": True,
        }
        response = self.client.post(reverse("v2:alias-list"), values, format="json")
        self.assertEqual(response.status_code, 201)
        alias = Alias.objects.get(address="foobar@test.com")
        self.assertTrue(
            alias.aliasrecipient_set.filter(
                address="user+spam@test.com",
                r_mailbox__isnull=False,
                r_alias__isnull=True,
            ).exists()
        )

    def test_utf8_alias(self):
        """Test alias with non-ASCII characters."""
        values = {
            "address": "testé@test.com",
            "recipients": ["user@test.com", "admin@test.com", "ext@titi.com"],
            "enabled": True,
        }
        response = self.client.post(reverse("v2:alias-list"), values, format="json")
        self.assertTrue(response.status_code, 201)

    def test_dlist(self):
        values = {
            "address": "all@test.com",
            "recipients": ["user@test.com", "admin@test.com", "ext@titi.com"],
            "enabled": True,
        }
        response = self.client.post(reverse("v2:alias-list"), values, format="json")
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="user@test.com")
        mb = user.mailbox
        self.assertEqual(
            AliasRecipient.objects.filter(alias__internal=False, r_mailbox=mb).count(),
            2,
        )
        admin = User.objects.get(username="admin@test.com")
        mb = admin.mailbox
        self.assertEqual(
            AliasRecipient.objects.filter(alias__internal=False, r_mailbox=mb).count(),
            1,
        )
        dlist = Alias.objects.get(address="all@test.com")
        self.assertEqual(dlist.recipients_count, 3)
        values["recipients"].remove("admin@test.com")
        response = self.client.put(
            reverse("v2:alias-detail", args=[dlist.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(dlist.recipients_count, 2)

    def test_forward_and_local_copies(self):
        values = {
            "address": "user@test.com",
            "recipients": ["rcpt@dest.com"],
            "enabled": True,
        }
        response = self.client.post(reverse("v2:alias-list"), values, format="json")
        self.assertEqual(response.status_code, 201)
        fwd = Alias.objects.get(address="user@test.com", internal=False)
        self.assertEqual(fwd.recipients_count, 1)

        values["recipients"] = ["rcpt@dest.com", "user@test.com"]
        response = self.client.put(
            reverse("v2:alias-detail", args=[fwd.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        fwd = Alias.objects.get(pk=fwd.pk)
        self.assertEqual(fwd.aliasrecipient_set.count(), 2)
        self.assertEqual(fwd.aliasrecipient_set.filter(r_alias__isnull=True).count(), 2)

    def test_wildcard_alias(self):
        """Test creation of a wildcard alias."""
        values = {
            "address": "@test.com",
            "recipients": ["user@test.com"],
            "enabled": True,
        }
        response = self.client.post(reverse("v2:alias-list"), values, format="json")
        self.assertEqual(response.status_code, 201)

    def test_distribution_list_deletion_on_user_update_bug(self):
        """This test demonstrates an issue with distribution list being
        deleted when one of the users which belong to that list is
        changed.

        """
        values = {
            "address": "list@test.com",
            "recipients": ["user@test.com", "admin@test.com"],
            "enabled": True,
        }
        response = self.client.post(reverse("v2:alias-list"), values, format="json")
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(username="user@test.com")
        values = {
            "username": user.username,
            "first_name": "Tester",
            "last_name": "Toto",
            "password": "Toto1234",
            "role": "SimpleUsers",
            "mailbox": {
                "use_domain_quota": True,
            },
            "is_active": True,
            "email": user.email,
            "language": "en",
        }
        response = self.client.put(
            reverse("v2:account-detail", args=[user.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Alias.objects.filter(address="list@test.com").exists())

    def test_domainadmin_restrictions(self):
        """Check that restrictions are applied."""
        admin = User.objects.get(username="admin@test.com")
        self.authenticate_user(admin)

        values = {
            "address": "titi@test2.com",
            "recipients": ["user@test.com"],
            "enabled": True,
        }
        response = self.client.post(reverse("v2:alias-list"), values, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["address"][0],
            "Permission denied.",
        )
