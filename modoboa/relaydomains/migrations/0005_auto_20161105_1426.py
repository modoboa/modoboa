# Generated by Django 1.9.5 on 2016-11-05 13:26
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("relaydomains", "0004_auto_20161105_1424"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="relaydomain",
            name="dates",
        ),
    ]
