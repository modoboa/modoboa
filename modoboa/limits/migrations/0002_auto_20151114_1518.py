from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("limits", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelTable(
            name="limit",
            table=None,
        ),
        migrations.AlterModelTable(
            name="limitspool",
            table=None,
        ),
    ]
