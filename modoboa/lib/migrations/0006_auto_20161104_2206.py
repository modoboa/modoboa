# Generated by Django 1.9.5 on 2016-11-04 21:06
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("lib", "0005_auto_20160416_1449"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Parameter",
        ),
        migrations.RemoveField(
            model_name="userparameter",
            name="user",
        ),
        migrations.DeleteModel(
            name="UserParameter",
        ),
    ]
