# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admin', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RelayDomain',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='The domain name', unique=True, max_length=100, verbose_name='name')),
                ('target_host', models.CharField(help_text='Remote destination of this domain', max_length=255, verbose_name='target host')),
                ('enabled', models.BooleanField(default=True, help_text='Check to activate this domain', verbose_name='enabled')),
                ('verify_recipients', models.BooleanField(default=False, help_text='Check for valid recipients', verbose_name='verify recipients')),
                ('dates', models.ForeignKey(to='admin.ObjectDates')),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RelayDomainAlias',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='The alias name', unique=True, max_length=100, verbose_name='name')),
                ('enabled', models.BooleanField(default=True, help_text='Check to activate this alias', verbose_name='enabled')),
                ('dates', models.ForeignKey(to='admin.ObjectDates')),
                ('target', models.ForeignKey(verbose_name='target', to='postfix_relay_domains.RelayDomain', help_text='The relay domain this alias points to')),
            ],
            options={
                'abstract': False,
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
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='relaydomain',
            name='service',
            field=models.ForeignKey(to='postfix_relay_domains.Service'),
            preserve_default=True,
        ),
    ]
