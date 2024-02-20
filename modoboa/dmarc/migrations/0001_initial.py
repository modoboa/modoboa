# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("admin", "0002_migrate_from_modoboa_admin"),
    ]

    operations = [
        migrations.CreateModel(
            name="Record",
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
                ("source_ip", models.GenericIPAddressField()),
                ("count", models.IntegerField()),
                (
                    "disposition",
                    models.CharField(
                        max_length=10,
                        choices=[
                            (b"none", "None"),
                            (b"quarantine", "Quarantine"),
                            (b"reject", "Reject"),
                        ],
                    ),
                ),
                (
                    "dkim_result",
                    models.CharField(
                        max_length=9,
                        choices=[
                            (b"none", "None"),
                            (b"neutral", "Neutral"),
                            (b"pass", "Pass"),
                            (b"fail", "Fail"),
                            (b"temperror", "Temporary error"),
                            (b"permerror", "Permanent error"),
                            (b"policy", "Policy"),
                        ],
                    ),
                ),
                (
                    "spf_result",
                    models.CharField(
                        max_length=9,
                        choices=[
                            (b"none", "None"),
                            (b"neutral", "Neutral"),
                            (b"pass", "Pass"),
                            (b"fail", "Fail"),
                            (b"temperror", "Temporary error"),
                            (b"permerror", "Permanent error"),
                            (b"softfail", "Soft failure"),
                        ],
                    ),
                ),
                ("reason_type", models.CharField(max_length=15, blank=True)),
                ("reason_comment", models.CharField(max_length=100, blank=True)),
                (
                    "header_from",
                    models.ForeignKey(to="admin.Domain", on_delete=models.CASCADE),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Report",
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
                ("report_id", models.CharField(max_length=100)),
                ("start_date", models.DateTimeField()),
                ("end_date", models.DateTimeField()),
                ("policy_domain", models.CharField(max_length=100)),
                ("policy_adkim", models.CharField(max_length=1)),
                ("policy_aspf", models.CharField(max_length=1)),
                ("policy_p", models.CharField(max_length=10)),
                ("policy_sp", models.CharField(max_length=10)),
                ("policy_pct", models.SmallIntegerField()),
            ],
            options={
                "permissions": (("view_report", "Can view report"),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Reporter",
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
                ("org_name", models.CharField(max_length=100)),
                ("email", models.EmailField(unique=True, max_length=254)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Result",
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
                    "type",
                    models.CharField(
                        max_length=4, choices=[(b"dkim", b"DKIM"), (b"spf", b"SPF")]
                    ),
                ),
                ("domain", models.CharField(max_length=100)),
                ("result", models.CharField(max_length=9)),
                (
                    "record",
                    models.ForeignKey(to="dmarc.Record", on_delete=models.CASCADE),
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name="report",
            name="reporter",
            field=models.ForeignKey(to="dmarc.Reporter", on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name="report",
            unique_together=set([("reporter", "report_id")]),
        ),
        migrations.AddField(
            model_name="record",
            name="report",
            field=models.ForeignKey(to="dmarc.Report", on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
