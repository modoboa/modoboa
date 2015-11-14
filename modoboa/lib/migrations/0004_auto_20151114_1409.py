# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def move_language_preference(apps, schema_editor):
    """Move language from parameters to User model."""
    UserParameter = apps.get_model("lib", "UserParameter")
    for uparam in UserParameter.objects.filter(name="core.LANG"):
        uparam.user.language = uparam.value
        uparam.user.save()
        uparam.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('lib', '0003_rename_parameters'),
        ('core', '0005_user_language'),
    ]

    operations = [
        migrations.RunPython(move_language_preference),
    ]
