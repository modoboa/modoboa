# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="emailaddress",
            name="type",
            field=models.CharField(
                choices=[("home", "Home"), ("work", "Work"), ("other", "Other")],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="phonenumber",
            name="type",
            field=models.CharField(
                choices=[
                    ("home", "Home"),
                    ("work", "Work"),
                    ("other", "Other"),
                    ("main", "Main"),
                    ("cellular", "Cellular"),
                    ("fax", "Fax"),
                    ("pager", "Pager"),
                ],
                max_length=20,
            ),
        ),
    ]
