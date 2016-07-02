# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin', '0002_migrate_from_modoboa_admin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aliasrecipient',
            name='address',
            field=models.EmailField(max_length=254),
        ),
    ]
