# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admin', '0002_migrate_from_modoboa_admin'),
    ]

    operations = [
        migrations.CreateModel(
            name='RelayDomain',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('target_host', models.CharField(help_text='Remote destination of this domain', max_length=255, verbose_name='target host')),
                ('verify_recipients', models.BooleanField(default=False, help_text='Check for valid recipients', verbose_name='verify recipients')),
                ('dates', models.ForeignKey(to='admin.ObjectDates', on_delete=models.CASCADE)),
                ('domain', models.OneToOneField(null=True, to='admin.Domain', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['domain__name'],
                'db_table': 'postfix_relay_domains_relaydomain',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='The service name', unique=True, max_length=100, verbose_name='name')),
            ],
            options={
                'db_table': 'postfix_relay_domains_service',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='relaydomain',
            name='service',
            field=models.ForeignKey(to='relaydomains.Service', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
