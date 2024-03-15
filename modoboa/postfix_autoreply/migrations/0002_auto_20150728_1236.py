# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("postfix_autoreply", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transport",
            name="domain",
            field=models.CharField(max_length=300, db_index=True),
            preserve_default=True,
        ),
    ]
