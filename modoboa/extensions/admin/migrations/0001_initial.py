# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Alias',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('address', models.CharField(help_text="The alias address (without the domain part). For a 'catch-all' address, just enter an * character.", max_length=254, verbose_name='address')),
                ('extmboxes', models.TextField(blank=True)),
                ('enabled', models.BooleanField(default=True, help_text='Check to activate this alias', verbose_name='enabled')),
                ('aliases', models.ManyToManyField(help_text='The aliases this alias points to', to='admin.Alias')),
            ],
            options={
                'ordering': ['domain__name', 'address'],
                'permissions': (('view_aliases', 'View aliases'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='The domain name', unique=True, max_length=100, verbose_name='name')),
                ('quota', models.IntegerField()),
                ('enabled', models.BooleanField(default=True, help_text='Check to activate this domain', verbose_name='enabled')),
            ],
            options={
                'ordering': ['name'],
                'permissions': (('view_domain', 'View domain'), ('view_domains', 'View domains')),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DomainAlias',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='The alias name', unique=True, max_length=100, verbose_name='name')),
                ('enabled', models.BooleanField(default=True, help_text='Check to activate this alias', verbose_name='enabled')),
            ],
            options={
                'permissions': (('view_domaliases', 'View domain aliases'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Mailbox',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('address', models.CharField(help_text='Mailbox address (without the @domain.tld part)', max_length=252, verbose_name='address')),
                ('quota', models.PositiveIntegerField()),
                ('use_domain_quota', models.BooleanField(default=False)),
            ],
            options={
                'permissions': (('view_mailboxes', 'View mailboxes'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailboxOperation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=20, choices=[(b'rename', b'rename'), (b'delete', b'delete')])),
                ('argument', models.TextField()),
                ('mailbox', models.ForeignKey(blank=True, to='admin.Mailbox', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ObjectDates',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creation', models.DateTimeField(auto_now_add=True)),
                ('last_modification', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Quota',
            fields=[
                ('username', models.EmailField(max_length=254, serialize=False, primary_key=True)),
                ('bytes', models.BigIntegerField(default=0)),
                ('messages', models.IntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='mailbox',
            name='dates',
            field=models.ForeignKey(to='admin.ObjectDates'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mailbox',
            name='domain',
            field=models.ForeignKey(to='admin.Domain'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mailbox',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='domainalias',
            name='dates',
            field=models.ForeignKey(to='admin.ObjectDates'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='domainalias',
            name='target',
            field=models.ForeignKey(verbose_name='target', to='admin.Domain', help_text='The domain this alias points to'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='domain',
            name='dates',
            field=models.ForeignKey(to='admin.ObjectDates'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alias',
            name='dates',
            field=models.ForeignKey(to='admin.ObjectDates'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alias',
            name='domain',
            field=models.ForeignKey(to='admin.Domain'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alias',
            name='mboxes',
            field=models.ManyToManyField(help_text='The mailboxes this alias points to', to='admin.Mailbox', verbose_name='mailboxes'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='alias',
            unique_together=set([('address', 'domain')]),
        ),
    ]
