"""Tests for the dovecot access layer."""

from unittest import mock

from django.test import SimpleTestCase, TestCase, override_settings

from modoboa.lib import dovecot

REST_SETTINGS = {
    "DOVECOT_OPERATION_MODE": "rest",
    "DOVEADM_API_URL": "https://imap.example.com:8080/doveadm/v1",
    "DOVEADM_API_KEY": "secret",
}


def http_response(payload, status_code=200):
    response = mock.Mock()
    response.status_code = status_code
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


class FactoryTestCase(SimpleTestCase):
    def test_default_mode(self):
        self.assertEqual(dovecot.get_dovecot_operation_mode(), "cmd")
        self.assertIsInstance(dovecot.get_dovecot_backend(), dovecot.DoveadmCmdBackend)

    @override_settings(**REST_SETTINGS)
    def test_rest_mode(self):
        self.assertIsInstance(dovecot.get_dovecot_backend(), dovecot.DoveadmHTTPBackend)

    @override_settings(DOVECOT_OPERATION_MODE="rest")
    def test_rest_mode_missing_settings(self):
        with self.assertRaises(dovecot.DoveadmError):
            dovecot.get_dovecot_backend()

    @override_settings(DOVECOT_OPERATION_MODE="rest", DOVEADM_API_URL="http://url")
    def test_rest_mode_missing_api_key(self):
        with self.assertRaises(dovecot.DoveadmError):
            dovecot.get_dovecot_backend()


class DoveadmCmdBackendTestCase(SimpleTestCase):
    def setUp(self):
        self.backend = dovecot.DoveadmCmdBackend()

    @mock.patch("modoboa.lib.dovecot.doveadm_cmd")
    def test_get_user_home(self, doveadm_cmd_mock):
        doveadm_cmd_mock.return_value = (0, b"/srv/vmail/domain/user\n")
        self.assertEqual(
            self.backend.get_user_home("user@domain"), "/srv/vmail/domain/user"
        )
        doveadm_cmd_mock.assert_called_with(["user", "-f", "home", "user@domain"])

    @mock.patch("modoboa.lib.dovecot.doveadm_cmd")
    def test_get_user_home_failure(self, doveadm_cmd_mock):
        doveadm_cmd_mock.return_value = (68, b"user not found")
        with self.assertRaises(dovecot.DoveadmError):
            self.backend.get_user_home("user@domain")
        doveadm_cmd_mock.side_effect = OSError("doveadm command not found")
        with self.assertRaises(dovecot.DoveadmError):
            self.backend.get_user_home("user@domain")

    @mock.patch("modoboa.lib.dovecot.doveadm_cmd")
    def test_move_message(self, doveadm_cmd_mock):
        doveadm_cmd_mock.return_value = (0, b"")
        self.backend.move_message("user@domain", "Sent", "Scheduled", "X-Hdr", "12")
        doveadm_cmd_mock.assert_called_with(
            [
                "move",
                "-u",
                "user@domain",
                "Sent",
                "mailbox",
                "Scheduled",
                "header",
                "X-Hdr",
                "12",
            ]
        )
        doveadm_cmd_mock.return_value = (75, b"error")
        with self.assertRaises(dovecot.DoveadmError):
            self.backend.move_message("user@domain", "Sent", "Scheduled", "X-Hdr", "12")

    @mock.patch("modoboa.lib.dovecot.doveadm_cmd")
    def test_delete_mailbox_if_empty(self, doveadm_cmd_mock):
        doveadm_cmd_mock.return_value = (0, b"")
        self.backend.delete_mailbox_if_empty("user@domain", "Scheduled")
        doveadm_cmd_mock.assert_called_with(
            ["mailbox", "delete", "-u", "user@domain", "-s", "-e", "Scheduled"]
        )

    @mock.patch("modoboa.lib.dovecot.doveadm_cmd")
    def test_list_password_schemes(self, doveadm_cmd_mock):
        doveadm_cmd_mock.return_value = (0, b"SHA512-CRYPT PLAIN")
        self.assertEqual(self.backend.list_password_schemes(), "SHA512-CRYPT PLAIN")
        doveadm_cmd_mock.assert_called_with(["pw", "-l"])


@override_settings(**REST_SETTINGS)
class DoveadmHTTPBackendTestCase(SimpleTestCase):
    @mock.patch("modoboa.lib.dovecot.requests.post")
    def test_get_user_home(self, post_mock):
        post_mock.return_value = http_response(
            [["doveadmResponse", [{"home": "/srv/vmail/domain/user"}], "c1"]]
        )
        backend = dovecot.DoveadmHTTPBackend()
        self.assertEqual(backend.get_user_home("user@domain"), "/srv/vmail/domain/user")
        args, kwargs = post_mock.call_args
        self.assertEqual(args[0], REST_SETTINGS["DOVEADM_API_URL"])
        self.assertEqual(
            kwargs["json"], [["user", {"userMask": ["user@domain"]}, "c1"]]
        )
        self.assertTrue(kwargs["headers"]["Authorization"].startswith("X-Dovecot-API "))

    @mock.patch("modoboa.lib.dovecot.requests.post")
    def test_get_user_home_nested_response(self, post_mock):
        post_mock.return_value = http_response(
            [
                [
                    "doveadmResponse",
                    [{"user@domain": {"home": "/srv/vmail/domain/user"}}],
                    "c1",
                ]
            ]
        )
        backend = dovecot.DoveadmHTTPBackend()
        self.assertEqual(backend.get_user_home("user@domain"), "/srv/vmail/domain/user")

    @mock.patch("modoboa.lib.dovecot.requests.post")
    def test_get_user_home_not_found(self, post_mock):
        post_mock.return_value = http_response([["doveadmResponse", [], "c1"]])
        backend = dovecot.DoveadmHTTPBackend()
        with self.assertRaises(dovecot.DoveadmError):
            backend.get_user_home("user@domain")

    @mock.patch("modoboa.lib.dovecot.requests.post")
    def test_command_error(self, post_mock):
        post_mock.return_value = http_response(
            [["error", {"type": "exitCode", "exitCode": 68}, "c1"]]
        )
        backend = dovecot.DoveadmHTTPBackend()
        with self.assertRaises(dovecot.DoveadmError):
            backend.get_user_home("user@domain")

    @mock.patch("modoboa.lib.dovecot.requests.post")
    def test_network_error(self, post_mock):
        import requests

        post_mock.side_effect = requests.ConnectionError("connection refused")
        backend = dovecot.DoveadmHTTPBackend()
        with self.assertRaises(dovecot.DoveadmError):
            backend.get_user_home("user@domain")

    @mock.patch("modoboa.lib.dovecot.requests.post")
    def test_move_message(self, post_mock):
        post_mock.return_value = http_response([["doveadmResponse", [], "c1"]])
        backend = dovecot.DoveadmHTTPBackend()
        backend.move_message("user@domain", "Sent", "Scheduled", "X-Hdr", "12")
        kwargs = post_mock.call_args[1]
        self.assertEqual(
            kwargs["json"],
            [
                [
                    "move",
                    {
                        "user": "user@domain",
                        "destinationMailbox": "Sent",
                        "query": ["mailbox", "Scheduled", "header", "X-Hdr", "12"],
                    },
                    "c1",
                ]
            ],
        )

    @mock.patch("modoboa.lib.dovecot.requests.post")
    def test_delete_mailbox_if_empty(self, post_mock):
        post_mock.return_value = http_response([["doveadmResponse", [], "c1"]])
        backend = dovecot.DoveadmHTTPBackend()
        backend.delete_mailbox_if_empty("user@domain", "Scheduled")
        kwargs = post_mock.call_args[1]
        self.assertEqual(
            kwargs["json"],
            [
                [
                    "mailboxDelete",
                    {
                        "user": "user@domain",
                        "mailbox": ["Scheduled"],
                        "requireEmpty": True,
                        "subscriptions": True,
                    },
                    "c1",
                ]
            ],
        )

    def test_list_password_schemes(self):
        backend = dovecot.DoveadmHTTPBackend()
        with self.assertRaises(dovecot.DoveadmError):
            backend.list_password_schemes()


class RestModeStructureTestCase(SimpleTestCase):
    """Check admin global parameters structure in rest mode."""

    @override_settings(**REST_SETTINGS)
    def test_handle_mailboxes_visible(self):
        from modoboa.admin.app_settings import init_structure

        structure = init_structure()
        self.assertIn("handle_mailboxes", structure["mailboxes"]["params"])


class RestModeSchemesTestCase(TestCase):
    """Check password schemes retrieval in rest mode."""

    @override_settings(**REST_SETTINGS)
    def test_get_dovecot_schemes_fallback(self):
        from modoboa.admin.models.alarm import Alarm
        from modoboa.core.constants import DOVEADM_PASS_SCHEME_ALARM
        from modoboa.core.password_hashers.utils import get_dovecot_schemes

        schemes, status = get_dovecot_schemes()
        self.assertEqual(schemes, ["{MD5-CRYPT}", "{PLAIN}"])
        self.assertEqual(status, 1)
        # No alarm must be opened in this case
        self.assertFalse(
            Alarm.objects.filter(internal_name=DOVEADM_PASS_SCHEME_ALARM).exists()
        )

    @override_settings(
        **REST_SETTINGS, DOVECOT_SUPPORTED_SCHEMES="SHA512-CRYPT ARGON2ID"
    )
    def test_get_dovecot_schemes_from_settings(self):
        from modoboa.core.password_hashers.utils import get_dovecot_schemes

        schemes, status = get_dovecot_schemes()
        self.assertEqual(schemes, ["{SHA512-CRYPT}", "{ARGON2ID}"])
        self.assertEqual(status, 1)
