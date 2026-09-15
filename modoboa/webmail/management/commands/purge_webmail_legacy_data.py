"""Remove the data left by previous versions of the webmail."""

import os
import shutil

from django.core.management.base import BaseCommand

from modoboa.lib.redis import get_redis_connection
from modoboa.webmail.lib import attachments
from modoboa.webmail.models import MessageAttachment

# Previous versions stored compose sessions in one hash per user
LEGACY_COMPOSE_SESSION_KEY_PREFIX = "webmail-"


class Command(BaseCommand):
    """Management command to purge legacy webmail data."""

    help = (  # NOQA:A003
        "Remove the attachments stored inside MEDIA_ROOT and the compose "
        "sessions stored in Redis by previous versions, then delete orphan "
        "attachments"
    )

    def purge_legacy_attachments(self) -> int:
        """Empty the legacy attachments directory, inside MEDIA_ROOT.

        Files still used by a scheduled message are moved to the
        attachments directory (in case the migration could not do it),
        the others come from compose sessions that no longer exist and
        are removed.

        :return: the number of removed files
        """
        legacy_dir = attachments.get_legacy_attachments_dir()
        if not os.path.isdir(legacy_dir):
            return 0
        used = {
            os.path.basename(name)
            for name in MessageAttachment.objects.values_list("file", flat=True)
        }
        removed = 0
        for entry in os.scandir(legacy_dir):
            if not entry.is_file():
                continue
            target = attachments.get_storage_path(entry.name)
            try:
                if entry.name in used and not os.path.exists(target):
                    os.makedirs(
                        attachments.get_attachments_dir(), mode=0o700, exist_ok=True
                    )
                    shutil.move(entry.path, target)
                    continue
                os.remove(entry.path)
            except OSError:
                continue
            removed += 1
        try:
            os.rmdir(legacy_dir)
        except OSError:
            pass
        return removed

    def purge_legacy_compose_sessions(self) -> int:
        """Delete compose sessions stored by previous versions.

        They were kept in one Redis hash per user, which never expired
        and is no longer read.

        :return: the number of removed keys
        """
        rclient = get_redis_connection(bytes)
        removed = 0
        for key in rclient.scan_iter(match=f"{LEGACY_COMPOSE_SESSION_KEY_PREFIX}*"):
            if rclient.type(key) == b"hash":
                removed += rclient.delete(key)
        return removed

    def handle(self, *args, **options):
        files = self.purge_legacy_attachments()
        self.stdout.write(f"{files} file(s) removed from the legacy directory")
        keys = self.purge_legacy_compose_sessions()
        self.stdout.write(f"{keys} legacy compose session key(s) removed")
        orphans = attachments.cleanup_orphan_attachments()
        self.stdout.write(f"{orphans} orphan attachment(s) removed")
