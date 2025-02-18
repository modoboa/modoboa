"""PDF credentials lib tests."""

import os
import shutil

from django.urls import reverse

from modoboa.admin import factories

from modoboa.lib.tests import ModoAPITestCase
from modoboa.lib.exceptions import InternalError

import modoboa.pdfcredentials.lib as lib
from subprocess import Popen, PIPE


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

    def test_pdf_decryption(self):
        """Test that PDFs are decrypted."""
        username = "toto1818@test.com"
        self._create_account(username)
        fname = os.path.join(self.workdir, f"{username}.pdf")
        self.assertTrue(os.path.exists(fname))
        filebuff = lib.decrypt_file(fname)
        self.assertIn(
            "application/pdf",
            Popen("/usr/bin/file -b --mime -", shell=True, stdout=PIPE, stdin=PIPE)
            .communicate(filebuff)[0]
            .strip()
            .decode(),
        )
        with open(fname) as file:
            with self.assertRaises(UnicodeDecodeError):
                Popen(
                    "/usr/bin/file -b --mime -", shell=True, stdout=PIPE, stdin=PIPE
                ).communicate(file.read(1024))[0].strip()
