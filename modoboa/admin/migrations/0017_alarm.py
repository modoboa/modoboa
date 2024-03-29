# Generated by Django 2.2.12 on 2020-09-11 07:46

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("admin", "0016_auto_20200602_1201"),
    ]

    operations = [
        migrations.CreateModel(
            name="Alarm",
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
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
                ("closed", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.IntegerField(
                        choices=[(1, "Opened"), (2, "Closed")], db_index=True, default=1
                    ),
                ),
                ("title", models.CharField(max_length=150)),
                ("internal_name", models.CharField(max_length=120)),
                (
                    "domain",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alarms",
                        to="admin.Domain",
                    ),
                ),
                (
                    "mailbox",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="alarms",
                        to="admin.Mailbox",
                    ),
                ),
            ],
            options={
                "ordering": ["created"],
            },
        ),
    ]
