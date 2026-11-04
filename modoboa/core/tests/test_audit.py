"""Structured audit trail tests."""

import datetime
import logging

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from modoboa.admin import (
    constants as admin_constants,
    factories as admin_factories,
    models as admin_models,
)
from modoboa.core.api.v2.tests import CORE_SETTINGS, DOVEADM_TEST_PATH, DOVECOT_USER
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


class CoverageAuditTestCase(ModoAPITestCase):
    """Operations that were missing from the audit trail."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        super().setUpTestData()
        admin_factories.populate_database()

    def test_alarm_changes(self):
        # Alarms are created by jobs, outside of any revision
        alarm = admin_models.Alarm.objects.create(
            domain=admin_models.Domain.objects.get(name="test.com"),
            mailbox=None,
            title="Alarm",
        )
        resp = self.client.patch(
            reverse("v2:alarm-switch", args=[alarm.pk]),
            {"status": admin_constants.ALARM_CLOSED},
        )
        self.assertEqual(resp.status_code, 204)
        # A first change of an object without version is not a creation
        self.assertFalse(models.Log.objects.filter(action="admin.alarm.created"))
        self.assertTrue(models.Log.objects.filter(action="admin.alarm.modified"))

        resp = self.client.post(
            reverse("v2:alarm-bulk-delete"), {"ids": [alarm.pk]}, format="json"
        )
        self.assertEqual(resp.status_code, 204)
        log = models.Log.objects.get(action="admin.alarm.deleted")
        self.assertEqual(log.domain, "test.com")

    def test_domain_administrators(self):
        domain = admin_models.Domain.objects.get(name="test.com")
        account = models.User.objects.get(username="admin@test2.com")
        for name, code in (("add", "admin_added"), ("remove", "admin_removed")):
            resp = self.client.post(
                reverse(f"v2:domain-{name}-administrator", args=[domain.pk]),
                {"account": account.pk},
                format="json",
            )
            self.assertEqual(resp.status_code, 200)
            log = models.Log.objects.get(action=f"admin.domain.{code}")
            self.assertEqual(log.domain, "test.com")
            self.assertEqual(log.extra, {"account": "admin@test2.com"})

    def test_forward(self):
        account = models.User.objects.get(username="user@test.com")
        self.authenticate_user(account)
        resp = self.client.post(
            reverse("v2:user_account-forward"),
            {"recipients": "dest@ext.com"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        log = models.Log.objects.get(action="admin.alias.created")
        self.assertEqual(log.actor, account)

    # Without doveadm (CI), only weak schemes are valid and the
    # sha512crypt of CORE_SETTINGS is refused: use the fake doveadm.
    @override_settings(
        DOVEADM_LOOKUP_PATH=[DOVEADM_TEST_PATH], DOVECOT_USER=DOVECOT_USER
    )
    def test_global_parameters(self):
        # Schemes may have been cached by another test of the process
        cache.delete("password_scheme_choice")
        url = reverse("v2:parameter-global-detail", args=["core"])
        data = dict(CORE_SETTINGS, log_maximum_age=123)
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        log = models.Log.objects.get(action="core.parameters.modified")
        self.assertEqual(log.extra["app"], "core")
        self.assertIn("log_maximum_age", log.extra["changed"])
        # Names only, never values
        self.assertNotIn("123", log.message)

        models.Log.objects.all().delete()
        resp = self.client.put(url, data, format="json")
        self.assertFalse(models.Log.objects.filter(action="core.parameters.modified"))

    def test_account_security_events(self):
        account = models.User.objects.get(username="user@test.com")
        self.authenticate_user(account)
        resp = self.client.post(
            reverse("v2:account-set-me-password"),
            {"password": "toto", "new_password": "Toto1234"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        log = models.Log.objects.get(action="core.password.changed")
        self.assertEqual(log.actor, account)
        self.assertEqual(log.logger, "modoboa.auth")

        self.authenticate_user(models.User.objects.get(username="admin"))
        url = reverse("v2:account-manage-api-token")
        # The test case already gave a token to admin
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.client.force_authenticate(models.User.objects.get(username="admin"))
        self.assertEqual(self.client.post(url).status_code, 201)
        self.assertTrue(models.Log.objects.filter(action="core.api_token.created"))
        self.assertTrue(models.Log.objects.filter(action="core.api_token.deleted"))


class AuditFiltersTestCase(ModoAPITestCase):

    def setUp(self):
        super().setUp()
        logger = logging.getLogger("modoboa.admin")
        logger.info("a", extra=audit("core.login.failed", actor_name="bob"))
        logger.info("b", extra=audit("core.login.succeeded", actor_name="alice"))
        old = models.Log.objects.get(message="a")
        old.date_created = timezone.now() - datetime.timedelta(days=10)
        old.save(update_fields=["date_created"])
        models.Log.objects.filter(message="b").update(domain="test.com")

    def get_messages(self, **params):
        resp = self.client.get(reverse("v2:log-list"), params)
        self.assertEqual(resp.status_code, 200)
        return sorted(entry["message"] for entry in resp.json()["results"])

    def test_filters(self):
        self.assertEqual(self.get_messages(action="core.login.failed"), ["a"])
        self.assertEqual(self.get_messages(actor_name="alice"), ["b"])
        self.assertEqual(self.get_messages(domain="test.com"), ["b"])
        week_ago = (timezone.localdate() - datetime.timedelta(days=7)).isoformat()
        self.assertNotIn("a", self.get_messages(date_from=week_ago))
        self.assertEqual(self.get_messages(date_to=week_ago), ["a"])
        # Bounds are inclusive
        today = timezone.localdate().isoformat()
        self.assertIn("b", self.get_messages(date_from=today, date_to=today))

    def test_iso_date(self):
        resp = self.client.get(reverse("v2:log-list"))
        entry = resp.json()["results"][0]
        # Parsed back without error: ISO 8601 with timezone
        self.assertIsNotNone(datetime.datetime.fromisoformat(entry["date_created"]))

    def test_actions_catalog(self):
        resp = self.client.get(reverse("v2:log-actions"))
        self.assertEqual(resp.status_code, 200)
        actions = resp.json()
        codes = [action["code"] for action in actions]
        self.assertIn("core.login.failed", codes)
        self.assertIn("admin.domain.deleted", codes)
        labels = [action["label"] for action in actions]
        self.assertEqual(labels, sorted(labels))

    def test_actions_catalog_requires_authentication(self):
        self.client.credentials()
        resp = self.client.get(reverse("v2:log-actions"))
        self.assertEqual(resp.status_code, 401)
