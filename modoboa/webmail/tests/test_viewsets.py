from datetime import timedelta
import getpass
from io import BytesIO
import os
import shutil
import tempfile
from unittest import mock

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time
from rq import SimpleWorker

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

import django_rq
from oauth2_provider.models import get_access_token_model, get_application_model

from modoboa.core import models as core_models
from modoboa.core.tests import utils
from modoboa.admin import factories as admin_factories
from modoboa.lib.tests import ModoAPITestCase
from modoboa.webmail import factories, jobs, models
from modoboa.webmail.lib.attachments import ComposeSessionManager
from modoboa.webmail.mocks import IMAP4Mock

Application = get_application_model()
AccessToken = get_access_token_model()

DOVEADM_TEST_PATH = utils.get_doveadm_test_path()
DOVECOT_USER = getpass.getuser()


def get_gif():
    """Return gif."""
    gif = BytesIO(
        b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00"
        b"\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    )
    gif.name = "image.gif"
    return gif


class WebmailTestCase(ModoAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        admin_factories.populate_database()
        cls.user = core_models.User.objects.get(username="user@test.com")
        cls.application = Application.objects.create(
            name="Test Application",
            redirect_uris="http://localhost",
            user=cls.user,
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )

        cls.access_token = AccessToken.objects.create(
            user=cls.user,
            scope="read write",
            expires=timezone.now() + timedelta(seconds=300),
            token="secret-access-token-key",
            application=cls.application,
        )

    def setUp(self):
        """Connect with a simpler user."""
        patcher = mock.patch("imaplib.IMAP4")
        self.mock_imap4 = patcher.start()
        self.mock_imap4.return_value = IMAP4Mock()
        self.addCleanup(patcher.stop)
        self.set_global_parameter("imap_port", 1435)
        self.workdir = tempfile.mkdtemp()
        os.mkdir(f"{self.workdir}/webmail")
        self.set_global_parameter("update_scheme", False, app="core")

    def tearDown(self):
        """Cleanup."""
        shutil.rmtree(self.workdir)

    def authenticate(self):
        self.client.credentials(Authorization="Bearer " + self.access_token.token)


class UserMailboxViewSetTestCase(WebmailTestCase):

    def test_list(self):
        self.authenticate()
        url = reverse("v2:webmail-mailbox-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["mailboxes"]), 5)

    def test_quota(self):
        self.authenticate()
        url = reverse("v2:webmail-mailbox-quota")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        response = self.client.get(f"{url}?mailbox=INBOX")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["usage"], -1)

    def test_unseen(self):
        self.authenticate()
        url = reverse("v2:webmail-mailbox-unseen")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        response = self.client.get(f"{url}?mailbox=INBOX")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["counter"], 10)

    def test_create(self):
        self.authenticate()
        url = reverse("v2:webmail-mailbox-list")
        body = {"name": "Test"}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 201)
        body = {"parent": "Test", "name": "Test"}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 201)

    def test_rename(self):
        self.authenticate()
        url = reverse("v2:webmail-mailbox-rename")
        body = {"name": "Test renamed", "oldname": "Test"}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 200)

    def test_compress(self):
        self.authenticate()
        url = reverse("v2:webmail-mailbox-compress")
        body = {"name": "INBOX"}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 204)

    def test_empty(self):
        self.authenticate()
        url = reverse("v2:webmail-mailbox-empty")
        body = {"name": "INBOX"}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 404)
        body = {"name": "Trash"}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 204)

    def test_delete(self):
        self.authenticate()
        url = reverse("v2:webmail-mailbox-delete")
        body = {"name": "Test"}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 204)


class UserEmailViewSetTestCase(WebmailTestCase):

    def test_listmailbox(self):
        """Check listmailbox action."""
        self.authenticate()
        url = reverse("v2:webmail-email-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["count"], 1)
        self.assertEqual(
            content["results"][0]["from_address"]["address"],
            "nguyen.antoine@wanadoo.fr",
        )

        response = self.client.get(f"{url}?search=Réception")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            content["results"][0]["from_address"]["address"],
            "nguyen.antoine@wanadoo.fr",
        )

    def test_getmailsource(self):
        """Try to display a message's source."""
        self.authenticate()
        url = reverse("v2:webmail-email-source")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        response = self.client.get(f"{url}?mailbox=INBOX&mailid=133872")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Message-ID", response.json()["source"])

    def test_move(self):
        self.authenticate()
        url = reverse("v2:webmail-email-move")
        body = {"source": "INBOX", "destination": "Junk", "selection": [1]}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

        body = {"source": "INBOX", "selection": [1]}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 400)

    def test_delete(self):
        self.authenticate()
        url = reverse("v2:webmail-email-delete")
        body = {"source": "INBOX", "selection": [1]}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

        body = {"source": "INBOX", "selection": ["truc"]}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 0)

    def test_mark_as_junk(self):
        self.authenticate()
        url = reverse("v2:webmail-email-mark-as-junk")
        body = {"source": "INBOX", "selection": [1]}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    def test_mark_as_not_junk(self):
        self.authenticate()
        url = reverse("v2:webmail-email-mark-as-not-junk")
        body = {"source": "INBOX", "selection": [1]}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    def test_flag(self):
        self.authenticate()
        url = reverse("v2:webmail-email-flag")
        for status in ["read", "unread", "flagged", "unflagged"]:
            body = {"mailbox": "INBOX", "selection": [1], "status": status}
            response = self.client.post(url, body, format="json")
            self.assertEqual(response.status_code, 200)

    def test_content(self):
        self.authenticate()
        url = reverse("v2:webmail-email-content")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Empty email
        response = self.client.get(f"{url}?mailbox=INBOX&mailid=33")
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.json()["body"], None)

        # Reply modifier
        response = self.client.get(f"{url}?mailbox=INBOX&mailid=46931&context=reply")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["subject"].startswith("Re:"))

        # Forward modifier
        response = self.client.get(f"{url}?mailbox=INBOX&mailid=46932&context=forward")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["subject"].startswith("Fwd:"))

        # Scheduled message
        response = self.client.get(f"{url}?mailbox=Scheduled&mailid=33")
        self.assertEqual(response.status_code, 200)
        self.assertIn("scheduled_datetime", response.json())

    def test_attachment(self):
        self.authenticate()
        url = reverse("v2:webmail-email-attachment")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        response = self.client.get(f"{url}?mailbox=INBOX&mailid=3444&partnum=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["Content-Disposition"], "attachment; filename=attachment"
        )


class ComposeSessionViewSetTestCase(WebmailTestCase):

    def _create_compose_session(self):
        url = reverse("v2:webmail-compose-session-list")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertIn("uid", response.json())
        return response.json()["uid"]

    def test_create(self):
        self.authenticate()
        self._create_compose_session()

    def test_get(self):
        self.authenticate()
        uid = self._create_compose_session()
        url = reverse("v2:webmail-compose-session-detail", args=[uid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_allowed_senders(self):
        self.authenticate()
        url = reverse("v2:webmail-compose-session-allowed-senders")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_attachments(self):
        self.authenticate()
        uid = self._create_compose_session()

        manager = ComposeSessionManager(self.user.username)
        self.set_global_parameters({"max_attachment_size": "10"})
        url = reverse("v2:webmail-compose-session-attachments", args=[uid])
        with self.settings(MEDIA_ROOT=self.workdir):
            response = self.client.post(url, {"attachment": get_gif()})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Attachment is too big", response.json()["attachment"][0])

        self.set_global_parameters({"max_attachment_size": "10K"})
        with self.settings(MEDIA_ROOT=self.workdir):
            response = self.client.post(url, {"attachment": get_gif()})
        self.assertEqual(response.status_code, 200)
        content = manager.get_content(uid)
        self.assertEqual(len(content["attachments"]), 1)
        name = content["attachments"][0]["tmpname"]
        path = f"{self.workdir}/webmail/{name}"
        self.assertTrue(os.path.exists(path))

        url = reverse("v2:webmail-compose-session-delete-attachment", args=[uid, name])
        with self.settings(MEDIA_ROOT=self.workdir):
            response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(os.path.exists(path))

    def test_delete_attachment(self):
        self.authenticate()
        uid = self._create_compose_session()

        url = reverse(
            "v2:webmail-compose-session-delete-attachment", args=[uid, "unknown"]
        )
        with self.settings(MEDIA_ROOT=self.workdir):
            response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_send(self):
        self.authenticate()
        uid = self._create_compose_session()

        # Upload an attachment
        url = reverse("v2:webmail-compose-session-attachments", args=[uid])
        with self.settings(MEDIA_ROOT=self.workdir):
            response = self.client.post(url, {"attachment": get_gif()})

            # Send the message
            url = reverse("v2:webmail-compose-session-send", args=[uid])
            response = self.client.post(
                url,
                {
                    "sender": self.user.email,
                    "to": ["test@example.test"],
                    "subject": "test",
                    "body": "Test",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, "user@test.com")

        # Try to send an email using HTML format
        uid = self._create_compose_session()
        url = reverse("v2:webmail-compose-session-send", args=[uid])

        self.user.first_name = "Antoine"
        self.user.last_name = "Nguyen"
        self.user.parameters.set_value("editor", "html")
        self.user.save()
        mail.outbox = []
        response = self.client.post(
            url,
            {
                "sender": self.user.email,
                "to": ["test@example.test"],
                "subject": "test",
                "body": "<p>Test</p>",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, '"Antoine Nguyen" <user@test.com>')

    @override_settings(
        DOVEADM_LOOKUP_PATH=[DOVEADM_TEST_PATH], DOVECOT_USER=DOVECOT_USER
    )
    def test_schedule_and_send(self):
        self.authenticate()
        uid = self._create_compose_session()
        # Upload an attachment
        url = reverse("v2:webmail-compose-session-attachments", args=[uid])
        with self.settings(MEDIA_ROOT=self.workdir):
            self.client.post(url, {"attachment": get_gif()})
            # Schedule the message too early
            scheduled_datetime = timezone.now()
            url = reverse("v2:webmail-compose-session-send", args=[uid])
            response = self.client.post(
                url,
                {
                    "sender": self.user.email,
                    "to": ["test@example.test"],
                    "subject": "test",
                    "body": "Test",
                    "scheduled_datetime": scheduled_datetime.isoformat(),
                },
                format="json",
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn("scheduled_datetime", response.json())

            scheduled_datetime = timezone.now() + relativedelta(hours=1)
            response = self.client.post(
                url,
                {
                    "sender": self.user.email,
                    "to": ["test@example.test"],
                    "cc": ["cc@example.test"],
                    "subject": "test",
                    "body": "Test",
                    "scheduled_datetime": scheduled_datetime.isoformat(),
                },
                format="json",
            )
            self.assertEqual(response.status_code, 204)
            self.assertEqual(len(mail.outbox), 0)
            self.assertEqual(models.ScheduledMessage.objects.count(), 1)
            self.assertEqual(models.MessageAttachment.objects.count(), 1)

            with freeze_time(scheduled_datetime + relativedelta(minutes=1)):
                jobs.send_scheduled_messages()
                queue = django_rq.get_queue("modoboa")
                worker = SimpleWorker([queue], connection=queue.connection)
                worker.work(burst=True)

            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(models.ScheduledMessage.objects.count(), 0)
            self.assertEqual(models.MessageAttachment.objects.count(), 0)


@override_settings(DOVEADM_LOOKUP_PATH=[DOVEADM_TEST_PATH], DOVECOT_USER=DOVECOT_USER)
class ScheduledMessageViewSetTestCase(WebmailTestCase):

    def setUp(self):
        super().setUp()
        self.message = factories.ScheduledMessageFactory(
            account=self.user, scheduled_datetime=timezone.now()
        )

    def test_listmailbox(self):
        self.authenticate()
        url = reverse("v2:webmail-email-list")
        response = self.client.get(f"{url}?mailbox=Scheduled")
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["count"], 1)
        self.assertEqual(content["results"][0]["scheduled_id"], 1123)
        self.assertIn("scheduled_datetime_raw", content["results"][0])

    def test_delete(self):
        self.authenticate()
        url = reverse("v2:webmail-scheduled-message-detail", args=[self.message.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(models.ScheduledMessage.objects.count(), 0)

    def test_update(self):
        self.authenticate()
        url = reverse("v2:webmail-scheduled-message-detail", args=[self.message.id])
        data = {"scheduled_datetime": timezone.now() + relativedelta(days=1)}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.message.refresh_from_db()
        self.assertEqual(self.message.imap_uid, 11)
