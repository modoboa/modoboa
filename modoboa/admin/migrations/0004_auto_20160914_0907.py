# Generated by Django 1.9.9 on 2016-09-14 09:07
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("admin", "0003_auto_20151118_1215"),
    ]

    operations = [
        migrations.CreateModel(
            name="DNSBLResult",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("provider", models.CharField(db_index=True, max_length=254)),
                ("status", models.CharField(blank=True, db_index=True, max_length=45)),
                (
                    "domain",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="admin.Domain"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MXRecord",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=254)),
                ("address", models.GenericIPAddressField()),
                ("managed", models.BooleanField(default=False)),
                ("updated", models.DateTimeField()),
                (
                    "domain",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="admin.Domain"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SenderAddress",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("address", models.EmailField(max_length=254)),
                (
                    "mailbox",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="admin.Mailbox"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="alias",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="alias",
            name="expire_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dnsblresult",
            name="mx",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="admin.MXRecord"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="senderaddress",
            unique_together=set([("address", "mailbox")]),
        ),
        migrations.AlterUniqueTogether(
            name="dnsblresult",
            unique_together=set([("domain", "provider", "mx")]),
        ),
    ]
