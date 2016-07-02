# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def rename_limits_parameters(apps, schema_editor):
    """Rename parameters."""
    Parameter = apps.get_model("lib", "Parameter")
    for param in Parameter.objects.filter(name__startswith="DEFLT_"):
        param.name = param.name.replace("DEFLT_", "DEFLT_USER_")
        param.save()


class Migration(migrations.Migration):

    dependencies = [
        ('lib', '0004_auto_20151114_1409'),
    ]

    operations = [
        migrations.RunPython(rename_limits_parameters)
    ]
