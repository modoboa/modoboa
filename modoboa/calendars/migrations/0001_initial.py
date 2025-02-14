# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("admin", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccessRule",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("read", models.BooleanField(default=False)),
                ("write", models.BooleanField(default=False)),
                ("last_update", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "radicale_accessrule",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="SharedCalendar",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                (
                    "domain",
                    models.ForeignKey(to="admin.Domain", on_delete=models.CASCADE),
                ),
            ],
            options={
                "abstract": False,
                "db_table": "radicale_sharedcalendar",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="UserCalendar",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                (
                    "mailbox",
                    models.ForeignKey(to="admin.Mailbox", on_delete=models.CASCADE),
                ),
            ],
            options={
                "abstract": False,
                "db_table": "radicale_usercalendar",
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name="accessrule",
            name="calendar",
            field=models.ForeignKey(
                related_name="rules",
                to="calendars.UserCalendar",
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="accessrule",
            name="mailbox",
            field=models.ForeignKey(to="admin.Mailbox", on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name="accessrule",
            unique_together=set([("mailbox", "calendar")]),
        ),
    ]
