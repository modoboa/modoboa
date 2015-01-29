# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from modoboa.lib.migration_tools import add_permissions_to_group

PERMISSIONS = [
    ["core", "user", "add_user"],
    ["core", "user", "change_user"],
    ["core", "user", "delete_user"],
    ["admin", "domain", "view_domain"],
    ["admin", "mailbox", "add_mailbox"],
    ["admin", "mailbox", "change_mailbox"],
    ["admin", "mailbox", "delete_mailbox"],
    ["admin", "alias", "add_alias"],
    ["admin", "alias", "change_alias"],
    ["admin", "alias", "delete_alias"],
    ["admin", "mailbox", "view_mailboxes"],
    ["admin", "alias", "view_aliases"],
    ["admin", "domainalias", "view_domainaliases"],
    ["admin", "domainalias", "add_domainalias"],
    ["admin", "domainalias", "change_domainalias"],
    ["admin", "domainalias", "delete_domainalias"]
]

def load_initial_data(apps, schema_editor):
    """Load initial data."""
    Group = apps.get_model("auth", "Group")
    dadmins = Group.objects.create(name="DomainAdmins")
    add_permissions_to_group(apps, dadmins, PERMISSIONS)
    Group.objects.create(name="SimpleUsers")


class Migration(migrations.Migration):

    dependencies = [
        ('admin', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data)
    ]
