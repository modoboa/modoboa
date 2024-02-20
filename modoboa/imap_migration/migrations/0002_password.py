# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("imap_migration", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="migration",
            name="_password",
            field=models.CharField(max_length=255),
        ),
    ]
