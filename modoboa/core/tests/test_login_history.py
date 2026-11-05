"""Login history of the current user."""

import logging

from django.urls import reverse

from modoboa.admin import factories as admin_factories
from modoboa.core import models
from modoboa.core.api.v2.viewsets import LOGIN_HISTORY_SIZE
from modoboa.core.loggers import audit
from modoboa.lib.tests import ModoAPITestCase


class LoginHistoryTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        super().setUpTestData()
        admin_factories.populate_database()
        cls.user = models.User.objects.get(username="user@test.com")

    def setUp(self):
        super().setUp()
        self.authenticate_user(self.user)

    def log(self, action, **kwargs):
        logging.getLogger("modoboa.auth").info(
            action, extra=audit(action, ip="10.0.0.1", **kwargs)
        )

    def get_history(self):
        resp = self.client.get(reverse("v2:account-login-history"))
        self.assertEqual(resp.status_code, 200)
        return resp.json()

    def test_history(self):
        other = models.User.objects.get(username="user@test2.com")
        self.log("core.login.succeeded", actor=self.user)
        # Failed attempts are matched on the typed username
        self.log("core.login.failed", actor_name="user@test.com")
        self.log("core.login.failed", actor_name="user@test2.com")
        self.log("core.login.succeeded", actor=other)
        # Not a login event
        self.log("core.password.changed", actor=self.user)
        history = self.get_history()
        self.assertEqual(
            [entry["action"] for entry in history],
            ["core.login.failed", "core.login.succeeded"],
        )
        self.assertEqual(
            set(history[0]), {"date_created", "action", "action_label", "ip_address"}
        )
        self.assertEqual(history[0]["ip_address"], "10.0.0.1")
        self.assertEqual(history[0]["action_label"], "Login failed")

    def test_history_is_limited(self):
        for _ in range(LOGIN_HISTORY_SIZE + 5):
            self.log("core.login.succeeded", actor=self.user)
        self.assertEqual(len(self.get_history()), LOGIN_HISTORY_SIZE)

    def test_requires_authentication(self):
        self.client.credentials()
        resp = self.client.get(reverse("v2:account-login-history"))
        self.assertEqual(resp.status_code, 401)
