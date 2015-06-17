# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_delete_extension'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='master_user',
            field=models.BooleanField(default=False, verbose_name='Allow mailboxes access'),
            preserve_default=True,
        ),
    ]
