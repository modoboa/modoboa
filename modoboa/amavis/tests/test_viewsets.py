import os
from unittest import mock

from rq import SimpleWorker

from django.core import mail
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

import django_rq

from modoboa.admin import factories as admin_factories, models as admin_models
from modoboa.amavis import factories, models
from modoboa.amavis.utils import smart_str
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoAPITestCase


AMAVIS_SETTINGS = {
    "localpart_is_case_sensitive": False,
    "recipient_delimiter": "+",
    "max_attachment_size": 14,
    "released_msgs_cleanup": False,
    "am_pdp_mode": "unix",
    "am_pdp_host": "localhost",
    "am_pdp_port": 9998,
    "user_can_release": False,
    "self_service": False,
    "manual_learning": True,
    "sa_is_local": True,
}


class TestDataMixin:
    """A mixin to provide test data."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create some content."""
        super().setUpTestData()
        cls.msgrcpt = factories.create_spam("user@test.com")


@override_settings(SA_LOOKUP_PATH=(os.path.dirname(__file__),))
class QuarantineViewSetTestCase(TestDataMixin, ModoAPITestCase):

    databases = "__all__"

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        admin_factories.populate_database()

    def tearDown(self):
        """Restore msgrcpt state."""
        self.msgrcpt.rs = " "
        self.msgrcpt.save(update_fields=["rs"])
        self.set_global_parameter("domain_level_learning", False)
        self.set_global_parameter("user_level_learning", False)

    def test_list(self):
        url = reverse("v2:amavis-quarantine-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        content = resp.json()
        self.assertEqual(content["count"], 1)

        resp = self.client.get(f"{url}?search=pouet&criteria=both")
        content = resp.json()
        self.assertEqual(content["count"], 0)

        resp = self.client.get(f"{url}?msgtype=V")
        content = resp.json()
        self.assertEqual(content["count"], 0)
        factories.create_virus("user@test.com")
        resp = self.client.get(f"{url}?msgtype=V")
        content = resp.json()
        self.assertEqual(content["count"], 1)

    def test_retrieve(self):
        mail_id = smart_str(self.msgrcpt.mail.mail_id)
        rcpt = smart_str(self.msgrcpt.rid.email)
        url = reverse("v2:amavis-quarantine-detail", args=[mail_id])
        resp = self.client.get(f"{url}?rcpt={rcpt}")
        self.assertEqual(resp.status_code, 200)

        user = core_models.User.objects.get(username="user@test.com")
        self.client.force_authenticate(user)
        resp = self.client.get(f"{url}?rcpt={rcpt}")
        self.assertEqual(resp.status_code, 200)
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, "V")

    def test_headers(self):
        mail_id = smart_str(self.msgrcpt.mail.mail_id)
        url = reverse("v2:amavis-quarantine-headers", args=[mail_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_headers_selfservice(self):
        self.client.logout()
        mail_id = smart_str(self.msgrcpt.mail.mail_id)
        url = reverse("v2:amavis-quarantine-headers", args=[mail_id])
        url = f"{url}?secret_id={smart_str(self.msgrcpt.mail.secret_id)}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        self.set_global_parameter("self_service", True)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        url = f"{url}&rcpt={smart_str(self.msgrcpt.rid.email)}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete(self):
        mail_id = smart_str(self.msgrcpt.mail.mail_id)
        url = reverse("v2:amavis-quarantine-delete", args=[mail_id])
        data = {"mailid": mail_id, "rcpt": smart_str(self.msgrcpt.rid.email)}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 204)
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, "D")

    def test_delete_selfservice(self):
        self.client.logout()
        mail_id = smart_str(self.msgrcpt.mail.mail_id)
        url = reverse("v2:amavis-quarantine-delete", args=[mail_id])
        data = {"mailid": mail_id, "rcpt": smart_str(self.msgrcpt.rid.email)}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 403)
        self.set_global_parameter("self_service", True)
        data["secret_id"] = smart_str(self.msgrcpt.mail.secret_id)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 204)
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, "D")

    def test_delete_selection(self):
        mail_id = smart_str(self.msgrcpt.mail.mail_id)
        url = reverse("v2:amavis-quarantine-delete-selection")
        data = {
            "selection": [
                {"mailid": mail_id, "rcpt": smart_str(self.msgrcpt.rid.email)}
            ]
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 204)
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, "D")

    @mock.patch("socket.socket")
    def test_release(self, mock_socket):
        mock_socket.return_value.recv.return_value = b"250 1234 Ok\r\n"
        mail_id = smart_str(self.msgrcpt.mail.mail_id)
        url = reverse("v2:amavis-quarantine-release", args=[mail_id])
        data = {"mailid": mail_id, "rcpt": smart_str(self.msgrcpt.rid.email)}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, "R")

    @mock.patch("socket.socket")
    def test_release_selfservice(self, mock_socket):
        """Test release view."""
        mock_socket.return_value.recv.return_value = b"250 1234 Ok\r\n"
        self.client.logout()
        mail_id = smart_str(self.msgrcpt.mail.mail_id)
        url = reverse("v2:amavis-quarantine-release", args=[mail_id])
        self.set_global_parameter("self_service", True)
        # Missing rcpt -> fails
        data = {"mailid": mail_id, "secret_id": "1234"}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 403)
        # Wrong secret_id -> fails
        data["rcpt"] = smart_str(self.msgrcpt.rid.email)
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 403)
        # Request mode
        data["secret_id"] = smart_str(self.msgrcpt.mail.secret_id)
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, "p")
        # Direct release mode
        self.set_global_parameter("user_can_release", True)
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, "R")

    def test_release_request(self):
        """Test release request mode."""
        user = core_models.User.objects.get(username="user@test.com")
        self.client.force_authenticate(user)

        mail_id = smart_str(self.msgrcpt.mail.mail_id)
        url = reverse("v2:amavis-quarantine-release", args=[mail_id])
        data = {"mailid": mail_id, "rcpt": smart_str(self.msgrcpt.rid.email)}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, "p")

        # Send notification to admins
        call_command("amnotify")
        self.assertEqual(len(mail.outbox), 1)

    def _test_mark_selection(self, action, status):
        """Mark message common code."""
        mail_id = smart_str(self.msgrcpt.mail.mail_id)
        url = reverse("v2:amavis-quarantine-mark-selection")
        data = {
            "selection": [
                {"mailid": mail_id, "rcpt": smart_str(self.msgrcpt.rid.email)}
            ],
            "type": action,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 204)
        queue = django_rq.get_queue("modoboa")
        worker = SimpleWorker([queue], connection=queue.connection)
        worker.work(burst=True)
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, status)

        self.msgrcpt.rs = " "
        self.msgrcpt.save(update_fields=["rs"])
        self.set_global_parameter("sa_is_local", False)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 204)
        worker.work(burst=True)
        self.msgrcpt.refresh_from_db()
        self.assertEqual(self.msgrcpt.rs, status)

    def test_mark_as_ham(self):
        """Test mark_as_ham view."""
        self._test_mark_selection("ham", "H")

        # Check domain level learning
        self.set_global_parameter("domain_level_learning", True)
        data = {
            "selection": [
                {
                    "rcpt": smart_str(self.msgrcpt.rid.email),
                    "mailid": smart_str(self.msgrcpt.mail.mail_id),
                },
            ],
            "type": "ham",
            "database": "domain",
        }
        url = reverse("v2:amavis-quarantine-mark-selection")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 204)

        # Check user level learning
        self.set_global_parameter("user_level_learning", True)
        data["database"] = "user"
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 204)

    def test_mark_as_spam(self):
        """Test mark_as_spam view."""
        self._test_mark_selection("spam", "S")

    def test_manual_learning_as_user(self):
        """Test learning when connected as a simple user."""
        user = core_models.User.objects.get(username="user@test.com")
        self.client.force_authenticate(user)
        mail_id = smart_str(self.msgrcpt.mail.mail_id)
        data = {
            "selection": [
                {"mailid": mail_id, "rcpt": smart_str(self.msgrcpt.rid.email)}
            ],
            "type": "ham",
        }
        url = reverse("v2:amavis-quarantine-mark-selection")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.set_global_parameter("user_level_learning", True)
        self._test_mark_selection("ham", "H")


class PolicyViewSetTestCase(ModoAPITestCase):

    databases = "__all__"

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        admin_factories.populate_database()

    def test_get_policy(self):
        domain = admin_models.Domain.objects.get(name="test.com")
        url = reverse("v2:amavis-policy-detail", args=[domain.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_update_policy(self):
        domain = admin_models.Domain.objects.get(name="test.com")
        data = {"bypass_virus_checks": "Y", "spam_tag2_level": 6}
        url = reverse("v2:amavis-policy-detail", args=[domain.pk])
        resp = self.client.patch(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        p = models.Policy.objects.get(users__email="@test.com")
        self.assertEqual(p.bypass_virus_checks, data["bypass_virus_checks"])
        self.assertEqual(p.spam_tag2_level, data["spam_tag2_level"])


class ParametersAPITestCase(ModoAPITestCase):

    def test_update(self):
        settings = AMAVIS_SETTINGS.copy()
        url = reverse("v2:parameter-global-detail", args=["amavis"])
        resp = self.client.put(url, settings, format="json")
        self.assertEqual(resp.status_code, 200)
