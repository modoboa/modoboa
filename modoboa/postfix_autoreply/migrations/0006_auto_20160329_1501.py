# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("postfix_autoreply", "0005_auto_20151202_1623"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transport",
            name="domain",
            field=models.CharField(max_length=253, db_index=True),
        ),
    ]
