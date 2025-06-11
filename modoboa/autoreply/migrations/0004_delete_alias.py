from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("autoreply", "0003_move_aliases"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Alias",
        ),
    ]
