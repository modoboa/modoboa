"""Command to re-encrypt stored credential documents.

Documents created before the switch to authenticated encryption use
AES-CBC with a key taken directly from ``SECRET_KEY``. This command
rewrites them using the current format (Fernet, purpose-derived key).
"""

import os

from django.core.management.base import BaseCommand

from modoboa.parameters import tools as param_tools

from ... import lib


class Command(BaseCommand):
    """Command definition."""

    help = "Re-encrypt legacy credential documents with the current format"

    def handle(self, *args, **options):
        """Command entry point."""
        storage_dir = param_tools.get_global_parameter(
            "storage_dir", app="pdfcredentials"
        )
        if not os.path.isdir(storage_dir):
            self.stdout.write(f"Storage directory {storage_dir} not found")
            return
        converted = 0
        for entry in os.scandir(storage_dir):
            if not entry.is_file() or not entry.name.endswith(".pdf"):
                continue
            with open(entry.path, "rb") as fp:
                magic = fp.read(len(lib.ENCRYPTED_FILE_MAGIC))
            if magic == lib.ENCRYPTED_FILE_MAGIC:
                continue
            try:
                content = lib.decrypt_file(entry.path)
            except Exception as exc:
                self.stderr.write(f"Failed to decrypt {entry.path}: {exc}")
                continue
            token = lib.cryptutils.get_fernet(lib.CRYPT_PURPOSE).encrypt(content)
            with open(entry.path, "wb") as fp:
                fp.write(lib.ENCRYPTED_FILE_MAGIC)
                fp.write(token)
            converted += 1
        self.stdout.write(f"{converted} document(s) re-encrypted")
