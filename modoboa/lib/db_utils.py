# coding: utf-8

from django.conf import settings
from django.db import connection
from django.utils.translation import ugettext as _

from modoboa.lib.exceptions import InternalError


def db_table_exists(table):
    """Check if table exists."""
    return table in connection.introspection.table_names()


def db_type(cname="default"):
    """Return the type of the *default* database

    Supported values : 'postgres', 'mysql', 'sqlite'

    :param str cname: connection name
    :return: a string or None
    """
    if cname not in settings.DATABASES:
        raise InternalError(
            _("Connection to database %s not configured" % cname))
    for t in ['postgres', 'mysql', 'sqlite']:
        if settings.DATABASES[cname]['ENGINE'].find(t) != -1:
            return t
    return None
