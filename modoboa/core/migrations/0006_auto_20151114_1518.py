# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_user_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone_number',
            field=models.CharField(max_length=128, null=True, verbose_name='Phone number', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='secondary_email',
            field=models.EmailField(help_text='An alternative e-mail address, can be used for recovery needs.', max_length=254, null=True, verbose_name='Secondary email', blank=True),
            preserve_default=True,
        ),
    ]
