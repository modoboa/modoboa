# Generated by Django 2.2.12 on 2020-12-04 08:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin", "0017_alarm"),
    ]

    operations = [
        migrations.AlterField(
            model_name="alarm",
            name="title",
            field=models.TextField(),
        ),
    ]
