# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from modoboa.core.extensions import exts_pool
from modoboa.lib.migration_tools import add_permissions_to_group


def load_initial_data(apps, schema_editor):
    """Load initial data."""

    permissions = [
        ("radicale", "usercalendar", "add_usercalendar"),
        ("radicale", "usercalendar", "change_usercalendar"),
        ("radicale", "usercalendar", "delete_usercalendar"),
        ("radicale", "sharedcalendar", "add_sharedcalendar"),
        ("radicale", "sharedcalendar", "change_sharedcalendar"),
        ("radicale", "sharedcalendar", "delete_sharedcalendar")
    ]

    add_permissions_to_group(apps, "DomainAdmins", permissions)
    if not exts_pool.is_extension_installed(
            "modoboa.extensions.limits"):
        return
    add_permissions_to_group(apps, "Resellers", permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('radicale', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data)
    ]
