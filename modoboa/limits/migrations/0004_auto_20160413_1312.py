# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('limits', '0003_auto_20160413_1046'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='limit',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='limit',
            name='pool',
        ),
        migrations.RemoveField(
            model_name='limitspool',
            name='user',
        ),
        migrations.DeleteModel(
            name='Limit',
        ),
        migrations.DeleteModel(
            name='LimitsPool',
        ),
    ]
