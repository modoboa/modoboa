"""Normalize legacy language codes stored on user profiles.

Migration 0027 changed the language *choices* (e.g. ``pt_BR`` -> ``pt-br``)
but never migrated the values already stored in the database. Those stale
codes don't match Django's locale names, so the ``Accept-Language`` header
the frontend forwards is ignored and the UI/API falls back to English.

This data migration maps every legacy code to its current equivalent.
"""

from django.db import migrations

# Old (stored) code -> current code in modoboa.core.constants.LANGUAGES.
LEGACY_LANGUAGE_CODES = {
    "el_GR": "el",
    "ja_JP": "ja",
    "pl_PL": "pl",
    "pt_BR": "pt-br",
    "pt_PT": "pt",
    "ro_RO": "ro",
    "tr_TR": "tr",
    "zh_TW": "zh-hant",
}


def normalize_language_codes(apps, schema_editor):
    User = apps.get_model("core", "User")
    for old_code, new_code in LEGACY_LANGUAGE_CODES.items():
        User.objects.filter(language=old_code).update(language=new_code)


def revert_language_codes(apps, schema_editor):
    User = apps.get_model("core", "User")
    for old_code, new_code in LEGACY_LANGUAGE_CODES.items():
        User.objects.filter(language=new_code).update(language=old_code)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0030_alter_user_managers"),
    ]

    operations = [
        migrations.RunPython(normalize_language_codes, revert_language_codes),
    ]
