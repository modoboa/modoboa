"""Structured audit trail tests."""

from django.urls import reverse

from modoboa.admin import factories as admin_factories, models as admin_models
from modoboa.core import models
from modoboa.lib.tests import ModoAPITestCase, ModoTestCase


class AuthAuditTestCase(ModoTestCase):

    def test_login_succeeded(self):
        self.client.logout()
        self.client.post(
            reverse("core:login"), {"username": "admin", "password": "password"}
        )
        log = models.Log.objects.get(action="core.login.succeeded")
        self.assertEqual(log.actor.username, "admin")
        self.assertEqual(log.actor_name, "admin")
        self.assertEqual(log.ip_address, "127.0.0.1")

    def test_login_failed(self):
        self.client.logout()
        username = "x" * 300
        self.client.post(
            reverse("core:login"), {"username": username, "password": "bad"}
        )
        log = models.Log.objects.get(action="core.login.failed")
        self.assertIsNone(log.actor)
        self.assertEqual(log.actor_name, username[:254])
        self.assertEqual(log.ip_address, "127.0.0.1")


class AdminAuditTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        super().setUpTestData()
        admin_factories.populate_database()

    def test_domain_lifecycle(self):
        resp = self.client.post(
            reverse("v2:domain-list"), {"name": "audit.tld"}, format="json"
        )
        self.assertEqual(resp.status_code, 201)
        domain = admin_models.Domain.objects.get(name="audit.tld")
        log = models.Log.objects.get(action="admin.domain.created")
        self.assertEqual(log.actor_name, "admin")
        self.assertEqual(log.domain, "audit.tld")
        self.assertEqual(log.object_id, domain.pk)
        self.assertEqual(log.content_type.model, "domain")

        resp = self.client.post(reverse("v2:domain-delete", args=[domain.pk]))
        self.assertEqual(resp.status_code, 204)
        log = models.Log.objects.get(action="admin.domain.deleted")
        # The name survives the domain removal
        self.assertEqual(log.domain, "audit.tld")
        self.assertEqual(log.object_id, domain.pk)

        resp = self.client.get(reverse("v2:log-list"))
        entry = next(
            e for e in resp.json()["results"] if e["action"] == "admin.domain.deleted"
        )
        self.assertEqual(entry["object_type"], "admin.domain")
        self.assertEqual(entry["domain"], "audit.tld")

    def test_mailbox_domain(self):
        mailbox = admin_models.Mailbox.objects.get(
            address="user", domain__name="test.com"
        )
        resp = self.client.patch(
            reverse("v1:account-detail", args=[mailbox.user.pk]),
            {"username": "user@test.com", "role": "SimpleUsers", "first_name": "Bob"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        # User objects are attached to their mailbox domain
        self.assertTrue(
            models.Log.objects.filter(
                action__startswith="core.user.", domain="test.com"
            ).exists()
        )
