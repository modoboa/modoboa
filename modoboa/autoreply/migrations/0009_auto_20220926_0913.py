from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("autoreply", "0008_delete_transport"),
    ]

    operations = [
        migrations.AlterField(
            model_name="arhistoric",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="armessage",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]
