# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Maddr',
            fields=[
                ('partition_tag', models.IntegerField(unique=True, null=True, blank=True)),
                ('id', models.BigIntegerField(serialize=False, primary_key=True)),
                ('email', models.CharField(unique=True, max_length=255)),
                ('domain', models.CharField(max_length=765)),
            ],
            options={
                'db_table': 'maddr',
                'managed': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Mailaddr',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('priority', models.IntegerField()),
                ('email', models.CharField(unique=True, max_length=255)),
            ],
            options={
                'db_table': 'mailaddr',
                'managed': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Msgs',
            fields=[
                ('partition_tag', models.IntegerField(null=True, blank=True)),
                ('mail_id', models.CharField(max_length=12, serialize=False, primary_key=True)),
                ('secret_id', models.CharField(max_length=12, blank=True)),
                ('am_id', models.CharField(max_length=60)),
                ('time_num', models.IntegerField()),
                ('time_iso', models.CharField(max_length=48)),
                ('policy', models.CharField(max_length=765, blank=True)),
                ('client_addr', models.CharField(max_length=765, blank=True)),
                ('size', models.IntegerField()),
                ('originating', models.CharField(max_length=3)),
                ('content', models.CharField(max_length=1, blank=True)),
                ('quar_type', models.CharField(max_length=1, blank=True)),
                ('quar_loc', models.CharField(max_length=255, blank=True)),
                ('dsn_sent', models.CharField(max_length=3, blank=True)),
                ('spam_level', models.FloatField(null=True, blank=True)),
                ('message_id', models.CharField(max_length=765, blank=True)),
                ('from_addr', models.CharField(max_length=765, blank=True)),
                ('subject', models.CharField(max_length=765, blank=True)),
                ('host', models.CharField(max_length=765)),
            ],
            options={
                'db_table': 'msgs',
                'managed': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Msgrcpt',
            fields=[
                ('partition_tag', models.IntegerField(null=True, blank=True)),
                ('mail', models.ForeignKey(primary_key=True, serialize=False, to='amavis.Msgs')),
                ('rseqnum', models.IntegerField(default=0)),
                ('is_local', models.CharField(max_length=3)),
                ('content', models.CharField(max_length=3)),
                ('ds', models.CharField(max_length=3)),
                ('rs', models.CharField(max_length=3)),
                ('bl', models.CharField(max_length=3, blank=True)),
                ('wl', models.CharField(max_length=3, blank=True)),
                ('bspam_level', models.FloatField(null=True, blank=True)),
                ('smtp_resp', models.CharField(max_length=765, blank=True)),
            ],
            options={
                'db_table': 'msgrcpt',
                'managed': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Policy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('policy_name', models.CharField(max_length=32, blank=True)),
                ('virus_lover', models.CharField(max_length=3, null=True, blank=True)),
                ('spam_lover', models.CharField(max_length=3, null=True, blank=True)),
                ('unchecked_lover', models.CharField(max_length=3, null=True, blank=True)),
                ('banned_files_lover', models.CharField(max_length=3, null=True, blank=True)),
                ('bad_header_lover', models.CharField(max_length=3, null=True, blank=True)),
                ('bypass_virus_checks', models.CharField(default=b'', choices=[(b'N', 'yes'), (b'Y', 'no'), (b'', 'default')], max_length=3, help_text="Bypass virus checks or not. Choose 'default' to use global settings.", null=True, verbose_name='Virus filter')),
                ('bypass_spam_checks', models.CharField(default=b'', choices=[(b'N', 'yes'), (b'Y', 'no'), (b'', 'default')], max_length=3, help_text="Bypass spam checks or not. Choose 'default' to use global settings.", null=True, verbose_name='Spam filter')),
                ('bypass_banned_checks', models.CharField(default=b'', choices=[(b'N', 'yes'), (b'Y', 'no'), (b'', 'default')], max_length=3, help_text="Bypass banned checks or not. Choose 'default' to use global settings.", null=True, verbose_name='Banned filter')),
                ('bypass_header_checks', models.CharField(max_length=3, null=True, blank=True)),
                ('virus_quarantine_to', models.CharField(max_length=192, null=True, blank=True)),
                ('spam_quarantine_to', models.CharField(max_length=192, null=True, blank=True)),
                ('banned_quarantine_to', models.CharField(max_length=192, null=True, blank=True)),
                ('unchecked_quarantine_to', models.CharField(max_length=192, null=True, blank=True)),
                ('bad_header_quarantine_to', models.CharField(max_length=192, null=True, blank=True)),
                ('clean_quarantine_to', models.CharField(max_length=192, null=True, blank=True)),
                ('archive_quarantine_to', models.CharField(max_length=192, null=True, blank=True)),
                ('spam_tag_level', models.FloatField(null=True, blank=True)),
                ('spam_tag2_level', models.FloatField(null=True, blank=True)),
                ('spam_tag3_level', models.FloatField(null=True, blank=True)),
                ('spam_kill_level', models.FloatField(null=True, blank=True)),
                ('spam_dsn_cutoff_level', models.FloatField(null=True, blank=True)),
                ('spam_quarantine_cutoff_level', models.FloatField(null=True, blank=True)),
                ('addr_extension_virus', models.CharField(max_length=192, null=True, blank=True)),
                ('addr_extension_spam', models.CharField(max_length=192, null=True, blank=True)),
                ('addr_extension_banned', models.CharField(max_length=192, null=True, blank=True)),
                ('addr_extension_bad_header', models.CharField(max_length=192, null=True, blank=True)),
                ('warnvirusrecip', models.CharField(max_length=3, null=True, blank=True)),
                ('warnbannedrecip', models.CharField(max_length=3, null=True, blank=True)),
                ('warnbadhrecip', models.CharField(max_length=3, null=True, blank=True)),
                ('newvirus_admin', models.CharField(max_length=192, null=True, blank=True)),
                ('virus_admin', models.CharField(max_length=192, null=True, blank=True)),
                ('banned_admin', models.CharField(max_length=192, null=True, blank=True)),
                ('bad_header_admin', models.CharField(max_length=192, null=True, blank=True)),
                ('spam_admin', models.CharField(max_length=192, null=True, blank=True)),
                ('spam_subject_tag', models.CharField(max_length=192, null=True, blank=True)),
                ('spam_subject_tag2', models.CharField(default=None, max_length=192, blank=True, help_text="Modify spam subject using the specified text. Choose 'default' to use global settings.", null=True, verbose_name='Spam marker')),
                ('spam_subject_tag3', models.CharField(max_length=192, null=True, blank=True)),
                ('message_size_limit', models.IntegerField(null=True, blank=True)),
                ('banned_rulenames', models.CharField(max_length=192, null=True, blank=True)),
                ('disclaimer_options', models.CharField(max_length=192, null=True, blank=True)),
                ('forward_method', models.CharField(max_length=192, null=True, blank=True)),
                ('sa_userconf', models.CharField(max_length=192, null=True, blank=True)),
                ('sa_username', models.CharField(max_length=192, null=True, blank=True)),
            ],
            options={
                'db_table': 'policy',
                'managed': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Quarantine',
            fields=[
                ('partition_tag', models.IntegerField(null=True, blank=True)),
                ('mail', models.ForeignKey(primary_key=True, serialize=False, to='amavis.Msgs')),
                ('chunk_ind', models.IntegerField()),
                ('mail_text', models.TextField()),
            ],
            options={
                'ordering': ['-mail__time_num'],
                'db_table': 'quarantine',
                'managed': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Users',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('priority', models.IntegerField()),
                ('email', models.CharField(unique=True, max_length=255)),
                ('fullname', models.CharField(max_length=765, blank=True)),
            ],
            options={
                'db_table': 'users',
                'managed': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Wblist',
            fields=[
                ('rid', models.IntegerField(serialize=False, primary_key=True)),
                ('sid', models.IntegerField(primary_key=True)),
                ('wb', models.CharField(max_length=30)),
            ],
            options={
                'db_table': 'wblist',
                'managed': False,
            },
            bases=(models.Model,),
        ),
    ]
