# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def load_initial_data(apps, schema_editor):
    """Load initial data."""
    User = apps.get_model("core", "User")
    user = User(username="admin", is_superuser=True)
    user.set_password("password")
    user.save()

    ObjectAccess = apps.get_model("core", "ObjectAccess")
    ObjectAccess.objects.create(user=user, content_object=user, is_owner=True)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data)
    ]
