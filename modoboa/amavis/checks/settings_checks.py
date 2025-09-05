from django.conf import settings
from django.core.checks import Warning, register
from django.db import connections
from django.utils.translation import gettext as _

W001 = Warning(
    _(
        "AMAVIS_DEFAULT_DATABASE_ENCODING does not match the character "
        "encoding used by the Amavis database."
    ),
    hint=_(
        "Check your database character encoding and set/update "
        "AMAVIS_DEFAULT_DATABASE_ENCODING."
    ),
    id="modoboa-amavis.W001",
)

W002 = Warning(
    _("Modoboa Amavis has not been tested using the selected database engine."),
    hint=_("Try using PostgreSQL, MySQL or MariaDB."),
    id="modoboa-amavis.W002",
)


@register(deploy=True)
def check_amavis_database_encoding(app_configs, **kwargs):
    """Ensure AMAVIS_DEFAULT_DATABASE_ENCODING is set to the correct value."""
    errors = []
    db_engine = settings.DATABASES["amavis"]["ENGINE"]
    sql_query = None
    if "postgresql" in db_engine:
        sql_query = (
            "SELECT pg_encoding_to_char(encoding) "
            "FROM pg_database "
            "WHERE datname = %s;"
        )
    elif "mysql" in db_engine:
        sql_query = (
            "SELECT DEFAULT_CHARACTER_SET_NAME "
            "FROM INFORMATION_SCHEMA.SCHEMATA "
            "WHERE SCHEMA_NAME = %s;"
        )
    elif "sqlite" in db_engine:
        sql_query = "PRAGMA encoding;"
    else:
        errors.append(W002)
        return errors

    with connections["amavis"].cursor() as cursor:
        if "sqlite" in db_engine:
            cursor.execute(sql_query)
        else:
            cursor.execute(sql_query, [settings.DATABASES["amavis"]["NAME"]])
        encoding = cursor.fetchone()[0]

    if encoding.lower() != settings.AMAVIS_DEFAULT_DATABASE_ENCODING.lower():
        errors.append(W001)

    return errors
