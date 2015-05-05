from django.core.urlresolvers import reverse
from modoboa.core.models import User
from modoboa.lib.tests import ModoTestCase
from modoboa.extensions.admin.models import (
    Alias
)
from modoboa.extensions.admin import factories


class AliasTestCase(ModoTestCase):
    fixtures = ["initial_users.json"]

    def setUp(self):
        super(AliasTestCase, self).setUp()
        factories.populate_database()

    def test_alias(self):
        user = User.objects.get(username="user@test.com")
        values = dict(
            username="user@test.com", role=user.group,
            is_active=user.is_active, email="user@test.com",
            aliases="toto@test.com", aliases_1="titi@test.com"
        )
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values
        )
        self.assertEqual(user.mailbox_set.all()[0].alias_set.count(), 2)

        del values["aliases_1"]
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values
        )
        self.assertEqual(user.mailbox_set.all()[0].alias_set.count(), 1)

    def test_upper_case_alias(self):
        """Try to create an upper case alias."""
        user = User.objects.get(username="user@test.com")
        values = dict(
            username="user@test.com", role=user.group,
            is_active=user.is_active, email="user@test.com",
            aliases="Toto@test.com"
        )
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values
        )
        self.assertEqual(user.mailbox_set.first().alias_set.count(), 1)
        self.assertEqual(
            user.mailbox_set.first().alias_set.first().full_address,
            "toto@test.com"
        )

        values = {
            "email": "Titi@test.com", "recipients": "user@test.com",
            "enabled": True
        }
        self.ajax_post(reverse("admin:alias_add"), values)
        self.assertEqual(
            user.mailbox_set.first().alias_set.first().full_address,
            "titi@test.com"
        )

    def test_append_alias_with_tag(self):
        """Try to create a alias with tag in recipient address"""
        user = User.objects.get(username="user@test.com")
        values = dict(
            username="user@test.com", role=user.group,
            is_active=user.is_active, email="user@test.com"
        )
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values
        )

        values = {
            "email": "foobar@test.com", "recipients": "user+spam@test.com",
            "enabled": True
        }
        self.ajax_post(reverse("admin:alias_add"), values)
        alias = Alias.objects.get(address="foobar", domain__name="test.com")
        self.assertEqual(alias.extmboxes, "user+spam@test.com")

    def test_dlist(self):
        values = dict(email="all@test.com",
                      recipients="user@test.com",
                      recipients_1="admin@test.com",
                      recipients_2="ext@titi.com",
                      enabled=True)
        self.ajax_post(
            reverse("admin:dlist_add"), values
        )
        user = User.objects.get(username="user@test.com")
        self.assertEqual(user.mailbox_set.all()[0].alias_set.count(), 2)
        admin = User.objects.get(username="admin@test.com")
        self.assertEqual(admin.mailbox_set.all()[0].alias_set.count(), 1)

        dlist = Alias.objects.get(address="all", domain__name="test.com")
        self.assertEqual(len(dlist.get_recipients()), 3)
        del values["recipients_1"]
        self.ajax_post(
            reverse("admin:alias_change", args=[dlist.id]),
            values
        )
        self.assertEqual(dlist.get_recipients_count(), 2)

        self.ajax_post(
            reverse("admin:alias_delete") + "?selection=%d" % dlist.id, {}
        )
        self.assertRaises(Alias.DoesNotExist, Alias.objects.get,
                          address="all", domain__name="test.com")

    def test_forward(self):
        values = dict(email="forward2@test.com", recipients="rcpt@dest.com")
        self.ajax_post(
            reverse("admin:forward_add"), values
        )
        fwd = Alias.objects.get(address="forward2", domain__name="test.com")
        self.assertEqual(fwd.get_recipients_count(), 1)

        values["recipients"] = "rcpt2@dest.com"
        self.ajax_post(
            reverse("admin:alias_change",
                    args=[fwd.id]),
            values
        )
        self.assertEqual(fwd.get_recipients_count(), 1)

        self.ajax_post(
            reverse("admin:alias_delete") + "?selection=%d" \
                % fwd.id, {}
        )
        self.assertRaises(Alias.DoesNotExist, Alias.objects.get,
                          address="forward2", domain__name="test.com")

    def test_forward_and_local_copies(self):
        values = dict(email="user@test.com", recipients="rcpt@dest.com")
        self.ajax_post(
            reverse("admin:forward_add"), values
        )
        fwd = Alias.objects.get(address="user", domain__name="test.com")
        self.assertEqual(fwd.get_recipients_count(), 1)

        values["recipients"] = "rcpt@dest.com"
        values["recipients_1"] = "user@test.com"
        self.ajax_post(
            reverse("admin:alias_change", args=[fwd.id]),
            values
        )
        fwd = Alias.objects.get(pk=fwd.pk)
        self.assertEqual(fwd.get_recipients_count(), 2)
        self.assertEqual(fwd.aliases.count(), 0)
