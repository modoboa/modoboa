"""Amavis tests."""

import os

from django.test import override_settings
from django.urls import reverse

from modoboa.admin import factories as admin_factories, models as admin_models
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoAPITestCase
from modoboa.transport import factories as tr_factories
from .. import factories, lib, models


class DomainTestCase(ModoAPITestCase):
    """Check that database is populated."""

    databases = "__all__"

    def setUp(self):
        """Initiate test context."""
        self.admin = core_models.User.objects.get(username="admin")

    def test_create_domain(self):
        """Test domain creation."""
        domain = admin_factories.DomainFactory(name="domain.test")
        name = f"@{domain.name}"
        policy = models.Policy.objects.get(policy_name=name)
        user = models.Users.objects.filter(policy=policy).first()
        self.assertIsNot(user, None)
        self.assertEqual(user.email, name)

        # Create a domain alias
        self.client.force_authenticate(self.admin)
        url = reverse("v2:domain_alias-list")
        data = {"name": "dalias.test", "target": domain.pk}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 201)
        name = "@dalias.test"
        self.assertFalse(models.Policy.objects.filter(policy_name=name).exists())
        user = models.Users.objects.get(email=name)
        self.assertEqual(user.policy, policy)

        # Delete domain alias
        url = reverse("v2:domain_alias-detail", args=[resp.json()["pk"]])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(models.Users.objects.filter(email=name).exists())

    def test_rename_domain(self):
        """Test domain rename."""
        domain = admin_factories.DomainFactory(name="domain.test")
        domain.name = "domain1.test"
        domain.save()
        name = f"@{domain.name}"
        self.assertTrue(models.Users.objects.filter(email=name).exists())
        self.assertTrue(models.Policy.objects.filter(policy_name=name).exists())

        # Now from form
        self.client.force_authenticate(self.admin)
        rdomain = admin_factories.DomainFactory(name="domain.relay", type="relaydomain")
        rdomain.transport = tr_factories.TransportFactory(
            pattern=rdomain.name,
            service="relay",
            _settings={
                "relay_target_host": "external.host.tld",
                "relay_target_port": "25",
                "relay_verify_recipients": False,
            },
        )
        rdomain.save()
        url = reverse("v2:domain-detail", args=[rdomain.pk])
        values = {
            "name": "domain2.relay",
            "quota": rdomain.quota,
            "default_mailbox_quota": rdomain.default_mailbox_quota,
            "type": "relaydomain",
            "enabled": rdomain.enabled,
            "transport": {
                "service": rdomain.transport.service,
                "settings": {
                    "relay_target_host": "127.0.0.1",
                    "relay_target_port": 25,
                },
            },
        }
        resp = self.client.put(url, values, format="json")
        self.assertTrue(resp.status_code, 200)

    def test_delete_domain(self):
        """Test domain removal."""
        domain = admin_factories.DomainFactory(name="domain.test")
        domain.delete(None)
        name = f"@{domain.name}"
        self.assertFalse(models.Users.objects.filter(email=name).exists())
        self.assertFalse(models.Policy.objects.filter(policy_name=name).exists())

    def test_update_domain_policy(self):
        """Check domain policy edition."""
        self.client.force_authenticate(self.admin)
        domain = admin_factories.DomainFactory(name="domain.test")
        url = reverse("v2:amavis-policy-detail", args=[domain.pk])
        custom_title = "This is SPAM!"
        data = {"bypass_virus_checks": "Y", "spam_subject_tag2": custom_title}
        resp = self.client.patch(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        name = f"@{domain.name}"
        policy = models.Policy.objects.get(policy_name=name)
        self.assertEqual(policy.spam_subject_tag2, custom_title)


@override_settings(SA_LOOKUP_PATH=(os.path.dirname(__file__),))
class ManualLearningTestCase(ModoAPITestCase):
    """Check manual learning mode."""

    databases = "__all__"

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        admin_factories.populate_database()

    def test_alias_creation(self):
        """Check alias creation."""
        self.set_global_parameter("user_level_learning", True)

        # Fake activation because we don't have test data yet for
        # amavis...
        lib.setup_manual_learning_for_mbox(
            admin_models.Mailbox.objects.get(address="user", domain__name="test.com")
        )
        lib.setup_manual_learning_for_mbox(
            admin_models.Mailbox.objects.get(address="admin", domain__name="test.com")
        )

        url = reverse("v2:alias-list")
        values = {
            "address": "alias1000@test.com",
            "recipients": ["admin@test.com"],
            "enabled": True,
        }
        resp = self.client.post(url, values, format="json")
        self.assertEqual(resp.status_code, 201)
        policy = models.Policy.objects.get(policy_name=values["recipients"][0])
        user = models.Users.objects.get(email=values["address"])
        self.assertEqual(user.policy, policy)

        values = {
            "address": "user@test.com",
            "recipients": ["admin@test.com"],
            "enabled": True,
        }
        resp = self.client.post(url, values, format="json")
        self.assertEqual(resp.status_code, 201)
        policy = models.Policy.objects.get(policy_name=values["recipients"][0])
        user = models.Users.objects.get(email=values["address"])
        self.assertEqual(user.policy, policy)

    def test_mailbox_rename(self):
        """Check rename case."""
        self.set_global_parameter("user_level_learning", True)

        lib.setup_manual_learning_for_mbox(
            admin_models.Mailbox.objects.get(address="user", domain__name="test.com")
        )

        user = core_models.User.objects.get(username="user@test.com")
        url = reverse("v2:account-detail", args=[user.pk])
        values = {
            "username": "user2@test.com",
            "role": "SimpleUsers",
            "mailbox": {"use_domain_quota": True},
        }
        resp = self.client.put(url, values, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(models.Users.objects.filter(email=values["username"]).exists())

    def test_learn_alias_spam_as_admin(self):
        """Check learning spam for an alias address as admin user."""
        user = core_models.User.objects.get(username="admin")
        recipient_db = "user"
        rcpt = "alias@test.com"
        sender = "spam@evil.corp"
        content = factories.SPAM_BODY.format(rcpt=rcpt, sender=sender)

        saclient = lib.SpamassassinClient(user, recipient_db)
        result = saclient.learn_spam(rcpt, content)
        self.assertTrue(result)

    def test_delete_catchall_alias(self):
        """Check that Users record is not deleted."""
        self.set_global_parameter("user_level_learning", True)

        # Fake activation because we don't have test data yet for
        # amavis...
        lib.setup_manual_learning_for_mbox(
            admin_models.Mailbox.objects.get(address="admin", domain__name="test.com")
        )

        url = reverse("v2:alias-list")
        values = {
            "address": "@test.com",
            "recipients": ["admin@test.com"],
            "enabled": True,
        }
        resp = self.client.post(url, values, format="json")
        self.assertTrue(resp.status_code, 201)

        alias = admin_models.Alias.objects.get(address="@test.com")
        url = reverse("v2:alias-detail", args=[alias.pk])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)
        self.assertTrue(models.Users.objects.get(email="@test.com"))
