# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("admin", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            name="Migration",
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
                ("_password", models.CharField(max_length=100)),
                (
                    "mailbox",
                    models.ForeignKey(to="admin.Mailbox", on_delete=models.CASCADE),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
