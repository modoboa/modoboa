"""Structured audit trail tests."""

import logging

from django.urls import reverse

from modoboa.admin import factories as admin_factories, models as admin_models
from modoboa.core import loggers, models, signals
from modoboa.core.loggers import audit, get_audit_actions, register_audit_action
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
        self.assertEqual(log.object_repr, "audit.tld")
        # A deletion is a normal operation, not an incident
        self.assertEqual(log.level, "INFO")

        resp = self.client.get(reverse("v2:log-list"))
        entry = next(
            e for e in resp.json()["results"] if e["action"] == "admin.domain.deleted"
        )
        self.assertEqual(entry["object_type"], "admin.domain")
        self.assertEqual(entry["domain"], "audit.tld")

    def test_message_is_not_translated(self):
        """Messages are written in English whatever the admin language."""
        resp = self.client.post(
            reverse("v2:domain-list"),
            {"name": "fr.tld"},
            format="json",
            HTTP_ACCEPT_LANGUAGE="fr",
        )
        self.assertEqual(resp.status_code, 201)
        log = models.Log.objects.get(action="admin.domain.created")
        self.assertEqual(log.message, "Domain 'fr.tld' created by user admin")

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


class AuditCatalogTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        super().setUpTestData()
        admin_factories.populate_database()

    def test_emitted_actions_are_declared(self):
        self.client.post(reverse("v2:domain-list"), {"name": "cat.tld"}, format="json")
        domain = admin_models.Domain.objects.get(name="cat.tld")
        self.client.post(reverse("v2:domain-delete", args=[domain.pk]))
        self.client.logout()
        self.client.post(reverse("core:login"), {"username": "admin", "password": "x"})
        actions = get_audit_actions()
        emitted = set(
            models.Log.objects.exclude(action="").values_list("action", flat=True)
        )
        self.assertIn("admin.domain.deleted", emitted)
        self.assertIn("core.login.failed", emitted)
        self.assertEqual(emitted - actions.keys(), set())

    def test_extension_action_label(self):
        register_audit_action("test.thing.done", "Thing done")
        self.addCleanup(loggers._AUDIT_ACTIONS.pop, "test.thing.done")
        logging.getLogger("modoboa.admin").info(
            "done", extra=audit("test.thing.done", actor_name="bot")
        )
        resp = self.client.get(reverse("v2:log-list"))
        entry = next(
            e for e in resp.json()["results"] if e["action"] == "test.thing.done"
        )
        self.assertEqual(entry["action_label"], "Thing done")


class AuditSignalTestCase(ModoTestCase):

    def test_signal_sent_for_audit_entries_only(self):
        received = []

        def receiver(sender, log, **kwargs):
            received.append(log)

        signals.audit_event_created.connect(receiver)
        self.addCleanup(signals.audit_event_created.disconnect, receiver)
        logger = logging.getLogger("modoboa.admin")
        logger.info("plain message")
        logger.info("audited", extra=audit("core.login.failed", actor_name="bob"))
        self.assertEqual([log.action for log in received], ["core.login.failed"])
        self.assertEqual(received[0].actor_name, "bob")

    def test_failing_receiver_does_not_break_operation(self):
        def receiver(sender, log, **kwargs):
            raise RuntimeError("boom")

        signals.audit_event_created.connect(receiver)
        self.addCleanup(signals.audit_event_created.disconnect, receiver)
        self.client.logout()
        with self.assertLogs("modoboa.audit", level="ERROR"):
            response = self.client.post(
                reverse("core:login"), {"username": "admin", "password": "password"}
            )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            models.Log.objects.filter(action="core.login.succeeded").exists()
        )
