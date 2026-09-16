"""Tests for the limits applied to the attachments of a message."""

from django.urls import reverse

from modoboa.webmail.lib.attachments import ComposeSessionManager
from modoboa.webmail.tests.test_viewsets import WebmailTestCase, get_gif


class AttachmentLimitsTestCase(WebmailTestCase):
    """A message is limited both in number and in total size."""

    def setUp(self):
        super().setUp()
        self.authenticate()
        url = reverse("v2:webmail-compose-session-list")
        self.uid = self.client.post(url).json()["uid"]
        self.url = reverse("v2:webmail-compose-session-attachments", args=[self.uid])
        self.manager = ComposeSessionManager(self.user.username)

    def _upload(self):
        with self.settings(MEDIA_ROOT=self.workdir):
            return self.client.post(self.url, {"attachment": get_gif()})

    def test_count_limit(self):
        self.set_global_parameters(
            {"max_attachment_size": "10K", "max_attachments_count": 2}
        )
        self.assertEqual(self._upload().status_code, 200)
        self.assertEqual(self._upload().status_code, 200)

        response = self._upload()
        self.assertEqual(response.status_code, 400)
        self.assertIn("more than 2", response.json()["attachment"][0])
        # The refused attachment was not saved
        self.assertEqual(len(self.manager.get_content(self.uid)["attachments"]), 2)

    def test_total_size_limit(self):
        # A single gif fits, two of them do not
        self.set_global_parameters(
            {
                "max_attachment_size": "10K",
                "max_attachments_total_size": "60",
                "max_attachments_count": 10,
            }
        )
        self.assertEqual(self._upload().status_code, 200)

        response = self._upload()
        self.assertEqual(response.status_code, 400)
        self.assertIn("whole message", response.json()["attachment"][0])
        self.assertEqual(len(self.manager.get_content(self.uid)["attachments"]), 1)

    def test_single_file_limit_still_applies(self):
        self.set_global_parameters(
            {"max_attachment_size": "10", "max_attachments_total_size": "10M"}
        )
        response = self._upload()
        self.assertEqual(response.status_code, 400)
        self.assertIn("Attachment is too big", response.json()["attachment"][0])
