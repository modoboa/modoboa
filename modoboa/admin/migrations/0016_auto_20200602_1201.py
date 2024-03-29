# Generated by Django 2.2.12 on 2020-06-02 10:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin", "0015_rename_view_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="domain",
            name="message_limit",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Number of messages this domain can send per day",
                null=True,
                verbose_name="Message sending limit",
            ),
        ),
        migrations.AddField(
            model_name="mailbox",
            name="message_limit",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Number of messages this mailbox can send per day",
                null=True,
                verbose_name="Message sending limit",
            ),
        ),
    ]
