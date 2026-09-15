"""Tests for the private attachments storage and resources cleanup."""

import importlib
from io import StringIO
import os
import time
from unittest import mock

from dateutil.relativedelta import relativedelta
from redis.exceptions import ConnectionError as RedisConnectionError

from django.apps import apps
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from modoboa.webmail import checks, factories, models
from modoboa.webmail.lib import attachments
from modoboa.webmail.lib.utils import make_body_images_inline
from modoboa.webmail.tests.test_viewsets import WebmailTestCase, get_gif


def _write_file(path: str, content: bytes = b"x", age: int = 0) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fp:
        fp.write(content)
    if age:
        past = time.time() - age
        os.utime(path, (past, past))
    return path


class AttachmentStorageTestCase(WebmailTestCase):
    """Attachments are stored outside MEDIA_ROOT and never served."""

    def setUp(self):
        super().setUp()
        self.attachments_dir = f"{self.workdir}/attachments"
        self.media_root = f"{self.workdir}/media"

    def test_default_directory_is_outside_media_root(self):
        with override_settings(
            WEBMAIL_ATTACHMENTS_ROOT=None,
            BASE_DIR=self.workdir,
            MEDIA_ROOT=self.media_root,
        ):
            path = attachments.get_attachments_dir()
        self.assertEqual(path, f"{self.workdir}/webmail_attachments")

    def test_storage_path_keeps_the_file_name_only(self):
        self.assertEqual(
            attachments.get_storage_path("../../etc/passwd"),
            f"{self.attachments_dir}/passwd",
        )

    def test_files_have_no_url(self):
        with self.assertRaises(ValueError):
            attachments.WebmailAttachmentStorage().url("tmpfile")

    def test_upload_is_stored_in_private_directory(self):
        self.authenticate()
        uid = self.client.post(reverse("v2:webmail-compose-session-list")).json()["uid"]
        url = reverse("v2:webmail-compose-session-attachments", args=[uid])
        with self.settings(MEDIA_ROOT=self.media_root):
            response = self.client.post(url, {"attachment": get_gif()})
        self.assertEqual(response.status_code, 200)
        tmpname = response.json()["tmpname"]
        self.assertTrue(os.path.isfile(f"{self.attachments_dir}/{tmpname}"))
        self.assertFalse(os.path.exists(self.media_root))

    def test_body_images_never_embed_private_files(self):
        """Another user's attachment can't be embedded by referencing its path."""
        _write_file(f"{self.attachments_dir}/tmpimage", get_gif().read())
        _write_file(f"{self.media_root}/webmail/tmplegacy", get_gif().read())
        _write_file(f"{self.workdir}/static/icon.gif", get_gif().read())
        with override_settings(BASE_DIR=self.workdir, MEDIA_ROOT=self.media_root):
            _, parts = make_body_images_inline(
                '<p><img src="/attachments/tmpimage">'
                '<img src="/media/webmail/tmplegacy"></p>'
            )
            self.assertEqual(parts, [])
            # A regular local image is still embedded
            _, parts = make_body_images_inline('<p><img src="/static/icon.gif"></p>')
            self.assertEqual(len(parts), 1)

    def test_migration_moves_existing_files(self):
        migration = importlib.import_module(
            "modoboa.webmail.migrations.0003_move_attachments_out_of_media"
        )
        _write_file(f"{self.media_root}/webmail/tmplegacy", b"legacy")
        message = factories.ScheduledMessageFactory(
            account=self.user, scheduled_datetime=timezone.now()
        )
        models.MessageAttachment.objects.create(
            message=message,
            file="tmplegacy",
            content_type="text/plain",
            filename="a.txt",
        )
        with override_settings(MEDIA_ROOT=self.media_root):
            migration.move_attachments_out_of_media(apps, None)
        self.assertFalse(os.path.exists(f"{self.media_root}/webmail/tmplegacy"))
        with open(f"{self.attachments_dir}/tmplegacy", "rb") as fp:
            self.assertEqual(fp.read(), b"legacy")


class ResourcesCleanupTestCase(WebmailTestCase):
    """Compose sessions expire and unused files are removed."""

    def setUp(self):
        super().setUp()
        self.attachments_dir = f"{self.workdir}/attachments"
        self.manager = attachments.ComposeSessionManager(self.user.username)

    def test_compose_session_expires(self):
        uid = self.manager.create()
        self.addCleanup(self.manager.delete, uid)
        key = self.manager._key(uid)
        ttl = self.manager.rclient.ttl(key)
        self.assertGreater(ttl, 0)
        self.assertLessEqual(ttl, attachments.COMPOSE_SESSION_TTL.total_seconds())
        # An active session is kept alive
        self.manager.rclient.expire(key, 10)
        self.manager.get_content(uid)
        self.assertGreater(self.manager.rclient.ttl(key), 10)

    def test_scheduling_drops_session_and_keeps_files(self):
        self.authenticate()
        uid = self.client.post(reverse("v2:webmail-compose-session-list")).json()["uid"]
        url = reverse("v2:webmail-compose-session-attachments", args=[uid])
        tmpname = self.client.post(url, {"attachment": get_gif()}).json()["tmpname"]
        path = f"{self.attachments_dir}/{tmpname}"

        url = reverse("v2:webmail-compose-session-send", args=[uid])
        response = self.client.post(
            url,
            {
                "sender": self.user.email,
                "to": ["test@example.test"],
                "subject": "test",
                "body": "Test",
                "scheduled_datetime": (
                    timezone.now() + relativedelta(hours=1)
                ).isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(self.manager.exists(uid))
        self.assertTrue(os.path.isfile(path))

        # Deleting the scheduled message (sent or cancelled) removes its files
        models.ScheduledMessage.objects.get().delete()
        self.assertFalse(os.path.exists(path))

    def test_cleanup_orphan_attachments(self):
        orphan = _write_file(f"{self.attachments_dir}/tmporphan", age=7200)
        recent = _write_file(f"{self.attachments_dir}/tmprecent", age=60)
        scheduled = _write_file(f"{self.attachments_dir}/tmpscheduled", age=7200)
        in_session = _write_file(f"{self.attachments_dir}/tmpsession", age=7200)

        message = factories.ScheduledMessageFactory(
            account=self.user, scheduled_datetime=timezone.now()
        )
        models.MessageAttachment.objects.create(
            message=message,
            file="tmpscheduled",
            content_type="text/plain",
            filename="a.txt",
        )
        uid = self.manager.create()
        self.addCleanup(self.manager.delete, uid)
        self.manager.set_content(
            uid,
            {
                "attachments": [
                    {
                        "fname": "b.txt",
                        "content-type": "text/plain",
                        "size": 1,
                        "tmpname": "tmpsession",
                    }
                ]
            },
        )

        self.assertEqual(attachments.cleanup_orphan_attachments(), 1)
        self.assertFalse(os.path.exists(orphan))
        for path in (recent, scheduled, in_session):
            self.assertTrue(os.path.exists(path), path)


class LegacyDataPurgeTestCase(WebmailTestCase):
    """Data stored by previous versions is purged on existing installations."""

    def setUp(self):
        super().setUp()
        self.attachments_dir = f"{self.workdir}/attachments"
        self.media_root = f"{self.workdir}/media"
        self.legacy_dir = f"{self.media_root}/webmail"
        media_root = self.settings(MEDIA_ROOT=self.media_root)
        media_root.enable()
        self.addCleanup(media_root.disable)
        self.rclient = attachments.get_redis_connection(bytes)

    def _schedule_attachment(self, name: str) -> None:
        message = factories.ScheduledMessageFactory(
            account=self.user, scheduled_datetime=timezone.now()
        )
        models.MessageAttachment.objects.create(
            message=message, file=name, content_type="text/plain", filename="a.txt"
        )

    def _purge(self) -> str:
        out = StringIO()
        call_command("purge_webmail_legacy_data", stdout=out)
        return out.getvalue()

    def test_purge_legacy_attachments(self):
        orphan = _write_file(f"{self.legacy_dir}/tmporphan")
        _write_file(f"{self.legacy_dir}/tmpnotmoved", b"scheduled")
        self._schedule_attachment("tmpnotmoved")

        self.assertIn("1 file(s) removed from the legacy directory", self._purge())
        self.assertFalse(os.path.exists(orphan))
        with open(f"{self.attachments_dir}/tmpnotmoved", "rb") as fp:
            self.assertEqual(fp.read(), b"scheduled")
        self.assertFalse(os.path.exists(self.legacy_dir))
        # Nothing left to do
        self.assertIn("0 file(s) removed from the legacy directory", self._purge())

    def test_purge_keeps_already_moved_files(self):
        _write_file(f"{self.legacy_dir}/tmpscheduled", b"copy")
        _write_file(f"{self.attachments_dir}/tmpscheduled", b"moved")
        self._schedule_attachment("tmpscheduled")

        self.assertIn("1 file(s) removed from the legacy directory", self._purge())
        with open(f"{self.attachments_dir}/tmpscheduled", "rb") as fp:
            self.assertEqual(fp.read(), b"moved")

    def test_purge_legacy_compose_sessions(self):
        legacy_key = "webmail-legacy@test.com"
        other_key = "webmail-not-a-session"
        self.rclient.hset(legacy_key, "uid", '{"attachments": []}')
        self.rclient.set(other_key, "value")
        self.addCleanup(self.rclient.delete, legacy_key, other_key)
        manager = attachments.ComposeSessionManager(self.user.username)
        uid = manager.create()
        self.addCleanup(manager.delete, uid)

        self._purge()
        self.assertFalse(self.rclient.exists(legacy_key))
        self.assertTrue(self.rclient.exists(other_key))
        self.assertTrue(manager.exists(uid))

    def test_purge_orphan_attachments(self):
        orphan = _write_file(f"{self.attachments_dir}/tmporphan", age=7200)

        self.assertIn("1 orphan attachment(s) removed", self._purge())
        self.assertFalse(os.path.exists(orphan))


class DeploymentChecksTestCase(WebmailTestCase):
    """Deployment checks point at unfinished upgrade steps."""

    def _scheduler(self, *func_names):
        scheduler = mock.Mock()
        scheduler.get_jobs.return_value = [
            mock.Mock(func_name=func_name) for func_name in func_names
        ]
        return scheduler

    @mock.patch("modoboa.webmail.checks.CronScheduler.all")
    def test_cleanup_job_not_registered(self, all_schedulers):
        all_schedulers.return_value = [
            self._scheduler("modoboa.webmail.jobs.send_scheduled_messages")
        ]
        self.assertEqual(checks.check_cleanup_job_is_registered(None), [checks.W001])

    @mock.patch("modoboa.webmail.checks.CronScheduler.all")
    def test_cleanup_job_registered(self, all_schedulers):
        all_schedulers.return_value = [
            self._scheduler("modoboa.webmail.jobs.send_scheduled_messages"),
            self._scheduler(checks.CLEANUP_JOB),
        ]
        self.assertEqual(checks.check_cleanup_job_is_registered(None), [])

    @mock.patch("modoboa.webmail.checks.CronScheduler.all")
    def test_no_scheduler_or_redis(self, all_schedulers):
        all_schedulers.return_value = []
        self.assertEqual(checks.check_cleanup_job_is_registered(None), [])
        all_schedulers.side_effect = RedisConnectionError
        self.assertEqual(checks.check_cleanup_job_is_registered(None), [])

    def test_legacy_attachments_dir(self):
        media_root = f"{self.workdir}/media"
        with override_settings(MEDIA_ROOT=media_root):
            self.assertEqual(checks.check_legacy_attachments_dir(None), [])
            os.makedirs(f"{media_root}/webmail")
            self.assertEqual(checks.check_legacy_attachments_dir(None), [checks.W002])
