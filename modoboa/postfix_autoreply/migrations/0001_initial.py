# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("admin", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            name="Alias",
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
                ("full_address", models.CharField(max_length=255)),
                ("autoreply_address", models.CharField(max_length=255)),
            ],
            options={
                "db_table": "postfix_autoreply_alias",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="ARhistoric",
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
                ("last_sent", models.DateTimeField(auto_now=True)),
                ("sender", models.CharField(max_length=254)),
            ],
            options={
                "db_table": "postfix_autoreply_arhistoric",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="ARmessage",
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
                (
                    "subject",
                    models.CharField(
                        help_text="The subject that will appear in sent emails",
                        max_length=255,
                        verbose_name="subject",
                    ),
                ),
                (
                    "content",
                    models.TextField(
                        help_text="The content that will appear in sent emails",
                        verbose_name="content",
                    ),
                ),
                (
                    "enabled",
                    models.BooleanField(
                        default=False,
                        help_text="Activate/Deactivate your auto reply",
                        verbose_name="enabled",
                    ),
                ),
                ("fromdate", models.DateTimeField(default=django.utils.timezone.now)),
                ("untildate", models.DateTimeField(null=True, blank=True)),
                (
                    "mbox",
                    models.ForeignKey(to="admin.Mailbox", on_delete=models.CASCADE),
                ),
            ],
            options={
                "db_table": "postfix_autoreply_armessage",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Transport",
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
                ("domain", models.CharField(max_length=300)),
                ("method", models.CharField(max_length=255)),
            ],
            options={
                "db_table": "postfix_autoreply_transport",
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name="arhistoric",
            name="armessage",
            field=models.ForeignKey(
                to="postfix_autoreply.ARmessage", on_delete=models.CASCADE
            ),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name="arhistoric",
            unique_together=set([("armessage", "sender")]),
        ),
    ]
