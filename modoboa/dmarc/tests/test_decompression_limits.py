"""Regression tests for decompression bomb protection (CWE-409/CWE-400)."""

import gzip
import io
import zipfile
from unittest import mock

from django.test import SimpleTestCase

from .. import lib


def _gzip_bytes(data: bytes) -> io.BytesIO:
    buf = io.BytesIO()
    with gzip.GzipFile(mode="wb", fileobj=buf) as fp:
        fp.write(data)
    buf.seek(0)
    return buf


def _zip_bytes(members: dict) -> io.BytesIO:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    buf.seek(0)
    return buf


@mock.patch.object(lib, "import_report")
class ImportArchiveLimitsTestCase(SimpleTestCase):
    """import_archive must reject oversized / abusive archives."""

    def test_gzip_within_limit_is_imported(self, import_report_mock):
        with mock.patch.object(lib, "MAX_DECOMPRESSED_SIZE", 1000):
            archive = _gzip_bytes(b"<feedback>ok</feedback>")
            lib.import_archive(archive, content_type="application/gzip")
        import_report_mock.assert_called_once_with(b"<feedback>ok</feedback>")

    def test_gzip_bomb_is_rejected(self, import_report_mock):
        with mock.patch.object(lib, "MAX_DECOMPRESSED_SIZE", 1000):
            # ~1 KB compressed expands to 2 MB of zeros.
            archive = _gzip_bytes(b"\x00" * (2 * 1024 * 1024))
            with self.assertRaises(ValueError):
                lib.import_archive(archive, content_type="application/gzip")
        import_report_mock.assert_not_called()

    def test_zip_member_too_large_is_rejected(self, import_report_mock):
        with mock.patch.object(lib, "MAX_DECOMPRESSED_SIZE", 1000):
            archive = _zip_bytes({"report.xml": b"\x00" * (2 * 1024 * 1024)})
            with self.assertRaises(ValueError):
                lib.import_archive(archive, content_type="application/zip")
        import_report_mock.assert_not_called()

    def test_zip_too_many_members_is_rejected(self, import_report_mock):
        with mock.patch.object(lib, "MAX_ZIP_MEMBERS", 3):
            members = {f"r{i}.xml": b"<feedback/>" for i in range(5)}
            archive = _zip_bytes(members)
            with self.assertRaises(ValueError):
                lib.import_archive(archive, content_type="application/zip")
        import_report_mock.assert_not_called()

    def test_zip_within_limits_is_imported(self, import_report_mock):
        with (
            mock.patch.object(lib, "MAX_DECOMPRESSED_SIZE", 1000),
            mock.patch.object(lib, "MAX_ZIP_MEMBERS", 5),
        ):
            archive = _zip_bytes({"report.xml": b"<feedback>ok</feedback>"})
            lib.import_archive(archive, content_type="application/zip")
        import_report_mock.assert_called_once_with(b"<feedback>ok</feedback>")


@mock.patch.object(lib, "import_archive")
class CompressedAttachmentSizeTestCase(SimpleTestCase):
    """import_report_from_email must reject oversized compressed attachments."""

    def _build_email(self, payload: bytes) -> str:
        import base64

        encoded = base64.b64encode(payload).decode()
        return (
            "MIME-Version: 1.0\n"
            'Content-Type: application/gzip; name="r.gz"\n'
            "Content-Transfer-Encoding: base64\n"
            "\n"
            f"{encoded}\n"
        )

    def test_oversized_compressed_attachment_is_rejected(self, import_archive_mock):
        with mock.patch.object(lib, "MAX_COMPRESSED_SIZE", 100):
            msg = self._build_email(b"\x00" * 500)
            with self.assertRaises(SystemExit) as ctx:
                lib.import_report_from_email(msg)
        self.assertEqual(ctx.exception.code, 65)
        import_archive_mock.assert_not_called()
