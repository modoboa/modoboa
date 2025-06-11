from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("autoreply", "0009_auto_20220926_0913"),
    ]

    operations = [
        migrations.AlterField(
            model_name="arhistoric",
            name="id",
            field=models.AutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="armessage",
            name="id",
            field=models.AutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]
