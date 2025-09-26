"""Tests for alias target allow/block settings."""

from django.urls import reverse

from modoboa.admin import factories, models
from modoboa.lib.tests import ModoAPITestCase


class AliasTargetSettingsTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        super().setUpTestData()
        factories.populate_database()

    def test_block_external_domain_when_any_allowed_with_block_list(self):
        # alias_can_target_any_domain = True and block external domain
        self.set_global_parameter("alias_can_target_any_domain", True, app="admin")
        self.set_global_parameter("alias_target_block_list", "bad.com", app="admin")

        values = {
            "address": "list@test.com",
            "recipients": ["user@bad.com"],
            "enabled": True,
        }
        resp = self.client.post(reverse("v2:alias-list"), values, format="json")
        # Creation should fail
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"], "Target domain not allowed: bad.com")

    def test_allow_only_list_when_any_disallowed(self):
        # alias_can_target_any_domain = False and allow list contains domain
        self.set_global_parameter("alias_can_target_any_domain", False, app="admin")
        self.set_global_parameter("alias_target_allow_list", "ok.com", app="admin")

        # Check if local domain is still allowed
        values = {
            "address": "list2@test.com",
            "recipients": ["user@test.com"],
            "enabled": True,
        }
        resp = self.client.post(reverse("v2:alias-list"), values, format="json")
        self.assertEqual(resp.status_code, 201)

        values = {
            "address": "list3@test.com",
            "recipients": ["user@ok.com"],
            "enabled": True,
        }
        resp = self.client.post(reverse("v2:alias-list"), values, format="json")
        self.assertEqual(resp.status_code, 201)
        alias = models.Alias.objects.get(address="list3@test.com", internal=False)
        # Allowed external domain should remain external
        self.assertTrue(
            alias.aliasrecipient_set.filter(
                address="user@ok.com", r_mailbox__isnull=True, r_alias__isnull=True
            ).exists()
        )

        # Now try a domain not in allow list, should stay external as well
        values = {
            "address": "list4@test.com",
            "recipients": ["user@bad.com"],
            "enabled": True,
        }
        resp = self.client.post(reverse("v2:alias-list"), values, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"], "Target domain not allowed: bad.com")
