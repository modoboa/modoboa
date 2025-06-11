from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("autoreply", "0007_auto_20180928_1423"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Transport",
        ),
    ]
