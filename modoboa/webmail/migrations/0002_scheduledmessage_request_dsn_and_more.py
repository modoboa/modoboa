from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("webmail", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="scheduledmessage",
            name="request_dsn",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="scheduledmessage",
            name="request_mdn",
            field=models.BooleanField(default=False),
        ),
    ]
