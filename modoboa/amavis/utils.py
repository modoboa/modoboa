"""A collection of utility functions for working with the Amavis database."""

import chardet

from django.conf import settings
from django.db.models.expressions import Func
from django.utils.encoding import (
    smart_bytes as django_smart_bytes,
    smart_str as django_smart_str,
)


"""
Byte fields for text data are EVIL.

MySQL uses `varbyte` fields which mysqlclient client maps to `str` (Py2) or
`bytes` (Py3), Djangos smart_* functions work as expected.

PostgreSQL uses `bytea` fields which psycopg2 maps to `memoryview`,
Djangos smart_* functions don't work as expected, you must call `tobytes()` on
the memoryview for them to work.

For convenience use smart_bytes and smart_str from this file in modoboa.amavis
to avoid any headaches.
"""


def smart_bytes(value, *args, **kwargs):
    if isinstance(value, memoryview):
        value = value.tobytes()
    return django_smart_bytes(value, *args, **kwargs)


def smart_str(value, *args, **kwargs):
    if isinstance(value, memoryview):
        value = value.tobytes()
    return django_smart_str(value, *args, **kwargs)


def fix_utf8_encoding(value):
    """Fix utf-8 strings that contain utf-8 escaped characters.

    msgs.from_addr and msgs.subject potentialy contain badly escaped utf-8
    characters, this utility function fixes that and should be used anytime
    these fields are accesses.

    Didn't even know the raw_unicode_escape encoding existed :)
    https://docs.python.org/3/library/codecs.html?highlight=raw_unicode_escape#python-specific-encodings
    """
    assert isinstance(value, str), "value should be of type str"

    if len(value) == 0:
        # short circuit for empty strings
        return ""

    bytes_value = value.encode("raw_unicode_escape")
    try:
        value = bytes_value.decode("utf-8")
    except UnicodeDecodeError:
        encoding = chardet.detect(bytes_value)
        try:
            value = bytes_value.decode(encoding["encoding"], "replace")
        except (TypeError, UnicodeDecodeError):
            # ??? use the original value, we've done our best to try and
            # convert it to a clean utf-8 string.
            pass

    return value


class ConvertFrom(Func):
    """Convert a binary value to a string.
    Calls the database specific function to convert a binary value to a string
    using the encoding set in AMAVIS_DEFAULT_DATABASE_ENCODING.
    """

    """PostgreSQL implementation.
    See https://www.postgresql.org/docs/9.3/static/functions-string.html#FUNCTIONS-STRING-OTHER"""  # NOQA:E501
    function = "convert_from"
    arity = 1
    template = (
        f"%(function)s(%(expressions)s, '{settings.AMAVIS_DEFAULT_DATABASE_ENCODING}')"
    )

    def as_mysql(self, compiler, connection):
        """MySQL implementation.
        See https://dev.mysql.com/doc/refman/5.5/en/cast-functions.html#function_convert
        """  # NOQA:E501
        return super().as_sql(
            compiler,
            connection,
            function="CONVERT",
            template=f"%(function)s(%(expressions)s USING {settings.AMAVIS_DEFAULT_DATABASE_ENCODING})",
            arity=1,
        )

    def as_sqlite(self, compiler, connection):
        """SQLite implementation.
        SQLite has no equivilant function, just return the field."""
        return super().as_sql(
            compiler,
            connection,
            template="%(expressions)s",
            arity=1,
        )
