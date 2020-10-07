"""Admin test cases."""

from django.urls import reverse

from modoboa.core.models import User
from modoboa.lib.tests import ModoTestCase
from .. import factories
from ..models import Alias, AliasRecipient, Domain


class AliasTestCase(ModoTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(AliasTestCase, cls).setUpTestData()
        factories.populate_database()

    def test_alias(self):
        user = User.objects.get(username="user@test.com")
        values = {
            "username": "user@test.com", "role": user.role,
            "is_active": user.is_active, "email": "user@test.com",
            "aliases": "toto@test.com", "aliases_1": "titi@test.com",
            "language": "en"
        }
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values
        )
        self.assertEqual(
            AliasRecipient.objects.filter
            (alias__internal=False, r_mailbox=user.mailbox)
            .count(), 2
        )
        del values["aliases_1"]
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values
        )
        self.assertEqual(
            AliasRecipient.objects.filter(
                alias__internal=False, r_mailbox=user.mailbox)
            .count(), 1
        )

    def test_alias_with_duplicated_recipient(self):
        """Check for duplicates."""
        values = {
            "address": "badalias@test.com",
            "recipients": "user@test.com",
            "recipients_1": "user@test.com",
            "enabled": True
        }
        self.ajax_post(
            reverse("admin:alias_add"), values
        )
        alias = Alias.objects.get(address="badalias@test.com")
        self.assertEqual(alias.recipients_count, 1)

    def test_upper_case_alias(self):
        """Try to create an upper case alias."""
        user = User.objects.get(username="user@test.com")
        values = {
            "username": "user@test.com", "role": user.role,
            "is_active": user.is_active, "email": "user@test.com",
            "aliases": "Toto@test.com", "language": "en"
        }
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values
        )
        mb = user.mailbox
        self.assertEqual(
            AliasRecipient.objects
            .filter(alias__internal=False, r_mailbox=mb).count(), 1)
        self.assertEqual(
            AliasRecipient.objects.get(
                alias__internal=False, r_mailbox=mb).alias.address,
            "toto@test.com"
        )

        values = {
            "address": "Titi@test.com", "recipients": "user@test.com",
            "enabled": True
        }
        self.ajax_post(reverse("admin:alias_add"), values)
        self.assertTrue(
            Alias.objects.filter(address="titi@test.com").exists())

    def test_append_alias_with_tag(self):
        """Try to create a alias with tag in recipient address"""
        user = User.objects.get(username="user@test.com")
        values = {
            "username": "user@test.com", "role": user.role,
            "is_active": user.is_active, "email": "user@test.com",
            "language": "en"
        }
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values
        )

        values = {
            "address": "foobar@test.com", "recipients": "user+spam@test.com",
            "enabled": True
        }
        self.ajax_post(reverse("admin:alias_add"), values)
        alias = Alias.objects.get(address="foobar@test.com")
        self.assertTrue(
            alias.aliasrecipient_set.filter(
                address="user+spam@test.com", r_mailbox__isnull=False,
                r_alias__isnull=True).exists()
        )

    def test_utf8_alias(self):
        """Test alias with non-ASCII characters."""
        values = {
            "address": "testé@test.com",
            "recipients": "user@test.com",
            "recipients_1": "admin@test.com",
            "recipients_2": "ext@titi.com",
            "enabled": True
        }
        self.ajax_post(
            reverse("admin:alias_add"), values
        )

    def test_dlist(self):
        values = {
            "address": "all@test.com",
            "recipients": "user@test.com",
            "recipients_1": "admin@test.com",
            "recipients_2": "ext@titi.com",
            "enabled": True
        }
        self.ajax_post(
            reverse("admin:alias_add"), values
        )
        user = User.objects.get(username="user@test.com")
        mb = user.mailbox
        self.assertEqual(
            AliasRecipient.objects.filter(
                alias__internal=False, r_mailbox=mb).count(), 2)
        admin = User.objects.get(username="admin@test.com")
        mb = admin.mailbox
        self.assertEqual(
            AliasRecipient.objects.filter(
                alias__internal=False, r_mailbox=mb).count(), 1)
        dlist = Alias.objects.get(address="all@test.com")
        self.assertEqual(dlist.recipients_count, 3)
        del values["recipients_1"]
        self.ajax_post(
            reverse("admin:alias_change", args=[dlist.id]),
            values
        )
        self.assertEqual(dlist.recipients_count, 2)

        self.ajax_post(
            "{}?selection={}".format(
                reverse("admin:alias_delete"), dlist.id),
            {}
        )
        self.assertRaises(
            Alias.DoesNotExist, Alias.objects.get, address="all@test.com")

    def test_forward(self):
        values = {"address": "forward2@test.com", "recipients": "rcpt@dest.com"}
        self.ajax_post(
            reverse("admin:alias_add"), values
        )
        fwd = Alias.objects.get(address="forward2@test.com")
        self.assertEqual(fwd.recipients_count, 1)

        values["recipients"] = "rcpt2@dest.com"
        self.ajax_post(
            reverse("admin:alias_change",
                    args=[fwd.id]),
            values
        )
        self.assertEqual(fwd.recipients_count, 1)

        self.ajax_post(
            reverse("admin:alias_delete") + "?selection=%d"
            % fwd.id, {}
        )
        self.assertRaises(
            Alias.DoesNotExist, Alias.objects.get, address="forward2@test.com")

    def test_forward_and_local_copies(self):
        values = {"address": "user@test.com", "recipients": "rcpt@dest.com"}
        self.ajax_post(
            reverse("admin:alias_add"), values
        )
        fwd = Alias.objects.get(address="user@test.com", internal=False)
        self.assertEqual(fwd.recipients_count, 1)

        values["recipients"] = "rcpt@dest.com"
        values["recipients_1"] = "user@test.com"
        self.ajax_post(
            reverse("admin:alias_change", args=[fwd.id]),
            values
        )
        fwd = Alias.objects.get(pk=fwd.pk)
        self.assertEqual(fwd.aliasrecipient_set.count(), 2)
        self.assertEqual(
            fwd.aliasrecipient_set.filter(r_alias__isnull=True).count(), 2)

    def test_wildcard_alias(self):
        """Test creation of a wildcard alias."""
        values = {
            "address": "@test.com",
            "recipients": "user@test.com",
            "enabled": True
        }
        self.ajax_post(
            reverse("admin:alias_add"), values
        )

    def test_random_alias(self):
        """Test creation of a random alias."""
        alias_count = Alias.objects.count()
        values = {
            "random_address": True,
            "domain": Domain.objects.get(name="test.com").pk,
            "recipients": "user@test.com",
            "enabled": True
        }
        self.ajax_post(reverse("admin:alias_add"), values)
        self.assertEqual(Alias.objects.count(), alias_count + 1)

        del values["domain"]
        content = self.ajax_post(reverse("admin:alias_add"), values, 400)
        self.assertIn("domain", content["form_errors"])

    def test_distribution_list_deletion_on_user_update_bug(self):
        """This test demonstrates an issue with distribution list being
           deleted when one of the users which belong to that list is
           changed.

        """
        values = {
            "address": "list@test.com",
            "recipients": "user@test.com",
            "recipients_1": "admin@test.com",
            "enabled": True
        }
        self.ajax_post(
            reverse("admin:alias_add"), values
        )

        user = User.objects.get(username="user@test.com")
        values = {
            "username": user.username, "first_name": "Tester",
            "last_name": "Toto", "password1": "Toto1234",
            "password2": "Toto1234", "role": "SimpleUsers", "quota_act": True,
            "is_active": True, "email": user.email, "language": "en"
        }
        self.ajax_post(reverse("admin:account_change", args=[user.id]), values)

        self.assertEqual(
            Alias.objects.filter(address="list@test.com").count(), 1)

    def test_alias_detail_view(self):
        """Test alias detail view."""
        account = Alias.objects.get(address="postmaster@test.com")
        url = reverse("admin:alias_detail", args=[account.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Summary", response.content.decode())
        self.assertIn("Recipients", response.content.decode())

    def test_domainadmin_restrictions(self):
        """Check that restrictions are applied."""
        admin = User.objects.get(username="admin@test.com")
        self.client.force_login(admin)

        user = User.objects.get(username="user@test.com")
        values = {
            "username": "user@test.com", "role": user.role,
            "is_active": user.is_active, "email": "user@test.com",
            "aliases": "toto@test.com", "aliases_1": "titi@test2.com",
            "language": "en"
        }
        response = self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values, 400
        )
        self.assertEqual(
            response["form_errors"]["aliases_1"][0],
            "You don't have access to this domain")
