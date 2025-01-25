# -*- coding: utf-8 -*-

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0004_auto_20181005_1415"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="contact",
            name="user",
        ),
        migrations.AlterField(
            model_name="contact",
            name="addressbook",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="contacts.AddressBook"
            ),
        ),
    ]
