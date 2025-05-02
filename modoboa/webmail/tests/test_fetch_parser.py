"""FETCH parser tests."""

import io
import unittest

from modoboa.webmail.lib.fetch_parser import FetchResponseParser

from . import data


def dump_bodystructure(fp, bs, depth=0):
    """Dump a parsed BODYSTRUCTURE."""
    indentation = " " * (depth * 4)
    for mp in bs:
        if isinstance(mp, list):
            if isinstance(mp[0], list):
                print(f"{indentation}multipart/{mp[1]}", file=fp)
                dump_bodystructure(fp, mp, depth + 1)
            else:
                dump_bodystructure(fp, mp, depth)
        elif isinstance(mp, dict):
            if isinstance(mp["struct"][0], list):
                print("{}multipart/{}".format(indentation, mp["struct"][1]), file=fp)
                dump_bodystructure(fp, mp["struct"][0], depth + 1)
            else:
                print("{}{}/{}".format(indentation, *mp["struct"][:2]), file=fp)
    fp.seek(0)
    result = fp.read()
    return result


class FetchParserTestCase(unittest.TestCase):
    """Test FETCH parser."""

    def setUp(self):
        """Setup test env."""
        self.parser = FetchResponseParser()

    def _test_bodystructure_output(self, bs, expected):
        """."""
        r = self.parser.parse(bs)
        fp = io.StringIO()
        output = dump_bodystructure(fp, r[list(r.keys())[0]]["BODYSTRUCTURE"])
        fp.close()
        self.assertEqual(output, expected)
        return r

    def test_parse_bodystructure(self):
        """Test the parsing of several responses containing BS."""
        self._test_bodystructure_output(
            data.BODYSTRUCTURE_SAMPLE_1,
            """multipart/alternative
    text/plain
    text/html
""",
        )
        self._test_bodystructure_output(
            data.BODYSTRUCTURE_SAMPLE_2,
            """multipart/mixed
    text/plain
    message/rfc822
""",
        )
        self._test_bodystructure_output(
            data.BODYSTRUCTURE_SAMPLE_3,
            """multipart/mixed
    multipart/alternative
        text/plain
        text/html
    application/pdf
""",
        )
        self._test_bodystructure_output(
            data.BODYSTRUCTURE_SAMPLE_4,
            """multipart/mixed
    multipart/alternative
        text/plain
        text/html
    application/octet-stream
""",
        )
        self._test_bodystructure_output(
            data.BODYSTRUCTURE_SAMPLE_5,
            """multipart/alternative
    text/plain
    text/html
""",
        )
        self._test_bodystructure_output(
            data.BODYSTRUCTURE_SAMPLE_6,
            """multipart/mixed
    multipart/related
        multipart/alternative
            text/plain
            text/html
        image/png
        image/jpeg
    application/pdf
    multipart/alternative
        text/plain
        text/html
""",
        )
        self._test_bodystructure_output(
            data.BODYSTRUCTURE_SAMPLE_7,
            """multipart/mixed
    multipart/mixed
        text/plain
    application/octet-stream
""",
        )
        self._test_bodystructure_output(data.BODYSTRUCTURE_SAMPLE_8, "text/html\n")
