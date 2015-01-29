# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import IntegrityError, models, migrations

from modoboa.lib.migration_tools import add_permissions_to_group
from modoboa.extensions.limits import controls


def load_initial_data(apps, schema_editor):
    """Load initial data."""
    ContentType = apps.get_model("contenttypes", "ContentType")
    Group = apps.get_model("auth", "Group")
    User = apps.get_model("core", "User")
    Domain = apps.get_model("admin", "Domain")

    ct = ContentType.objects.get(app_label="admin", model="domain")
    dagrp = Group.objects.get(name="DomainAdmins")

    grp = Group(name="Resellers")
    grp.save()
    grp.permissions.add(*dagrp.permissions.all())

    ct = ContentType.objects.get_for_model(Domain)
    add_permissions_to_group(
        apps, "Resellers", [("admin", "domain", "view_domains"),
                            ("admin", "domain", "add_domain"),
                            ("admin", "domain", "change_domain"),
                            ("admin", "domain", "delete_domain")]
    )

    for user in User.objects.filter(groups__name='DomainAdmins'):
        try:
            controls.create_pool(user)
        except IntegrityError:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('limits', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data)
    ]
