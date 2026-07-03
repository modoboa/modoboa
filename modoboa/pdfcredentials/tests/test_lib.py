"""PDF credentials lib tests."""

import base64
from io import BytesIO
import os
import shutil
import struct

from cryptography.fernet import InvalidToken

from django.core.management import call_command
from django.urls import reverse

from modoboa.admin import factories

from modoboa.lib.tests import ModoAPITestCase
from modoboa.lib.exceptions import InternalError

import modoboa.pdfcredentials.lib as lib


class PDFCredentialsLibTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def tearDown(self):
        """Reset test env."""
        shutil.rmtree(self.workdir)

    def _create_account(self, username, expected_status=201):
        url = reverse("v2:account-list")
        data = {
            "username": f"{username}",
            "role": "SimpleUsers",
            "mailbox": {"use_domain_quota": True},
            "password": "Toto12345",
            "language": "fr",
        }
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, expected_status)
        return data

    def test_storage_dir_setting(self):
        """Test multiple possibilities with storage_dir setup"""
        self.set_global_parameter("storage_dir", "/I_DONT_EXIST")
        with self.assertRaises(InternalError):
            lib.init_storage_dir()
        self.set_global_parameter("storage_dir", "/root")
        with self.assertRaises(InternalError):
            lib.init_storage_dir()
        self.set_global_parameter("storage_dir", self.workdir)
        self.assertIsNone(lib.init_storage_dir())

    def _write_legacy_file(self, fname, data):
        """Store data using the old AES-CBC format."""
        iv = os.urandom(16)
        encryptor = lib._get_legacy_cipher(iv).encryptor()
        if len(data) % 16:
            padded = data + b" " * (16 - len(data) % 16)
        else:
            padded = data
        with open(fname, "wb") as fp:
            fp.write(struct.pack(b"<Q", len(data)))
            fp.write(iv)
            fp.write(encryptor.update(padded) + encryptor.finalize())

    def test_encrypt_decrypt_roundtrip(self):
        """New files must use the authenticated format."""
        data = b"%PDF-1.4 fake content"
        fname = os.path.join(self.workdir, "new@test.com.pdf")
        lib.crypt_and_save_to_file(BytesIO(data), fname, len(data))
        with open(fname, "rb") as fp:
            self.assertTrue(fp.read().startswith(lib.ENCRYPTED_FILE_MAGIC))
        self.assertEqual(lib.decrypt_file(fname), data)

    def test_tampered_file_rejected(self):
        """A modified encrypted file must not decrypt."""
        data = b"%PDF-1.4 fake content"
        fname = os.path.join(self.workdir, "new@test.com.pdf")
        lib.crypt_and_save_to_file(BytesIO(data), fname, len(data))
        with open(fname, "rb") as fp:
            content = fp.read()
        # Flip one bit of the decoded token: flipping an encoded (base64)
        # character instead could only touch its unused padding bits and
        # leave the authenticated payload intact.
        token = bytearray(
            base64.urlsafe_b64decode(content[len(lib.ENCRYPTED_FILE_MAGIC) :])
        )
        token[-2] ^= 0x01
        with open(fname, "wb") as fp:
            fp.write(lib.ENCRYPTED_FILE_MAGIC)
            fp.write(base64.urlsafe_b64encode(token))
        with self.assertRaises(InvalidToken):
            lib.decrypt_file(fname)

    def test_legacy_file_decryption(self):
        """Files stored with the old AES-CBC format must still decrypt."""
        data = b"%PDF-1.4 fake content"
        fname = os.path.join(self.workdir, "legacy@test.com.pdf")
        self._write_legacy_file(fname, data)
        self.assertEqual(lib.decrypt_file(fname), data)

    def test_reencrypt_command(self):
        """Legacy files must be converted to the authenticated format."""
        self.set_global_parameter("storage_dir", self.workdir)
        data = b"%PDF-1.4 fake content"
        fname = os.path.join(self.workdir, "legacy@test.com.pdf")
        self._write_legacy_file(fname, data)
        call_command("reencrypt_pdf_credentials")
        with open(fname, "rb") as fp:
            self.assertTrue(fp.read().startswith(lib.ENCRYPTED_FILE_MAGIC))
        self.assertEqual(lib.decrypt_file(fname), data)
        # Running it again must be a no-op
        call_command("reencrypt_pdf_credentials")
        self.assertEqual(lib.decrypt_file(fname), data)

    def test_creds_filename_rejects_traversal(self):
        """A username must not allow escaping the storage directory."""
        self.set_global_parameter("storage_dir", self.workdir)

        class FakeAccount:
            username = "../outside"

        with self.assertRaises(InternalError):
            lib.get_creds_filename(FakeAccount())
        # Deletion must stay silent for such accounts
        self.assertIsNone(lib.delete_credentials(FakeAccount()))

    def test_pdf_decryption(self):
        """Test that PDFs are decrypted."""
        username = "toto1818@test.com"
        self._create_account(username)
        fname = os.path.join(self.workdir, f"{username}.pdf")
        self.assertTrue(os.path.exists(fname))
        filebuff = lib.decrypt_file(fname)
        self.assertTrue(filebuff.startswith(b"%PDF"))
        # The stored file must not contain the plaintext document
        with open(fname, "rb") as file:
            raw = file.read()
        self.assertTrue(raw.startswith(lib.ENCRYPTED_FILE_MAGIC))
        self.assertNotIn(b"%PDF", raw)
