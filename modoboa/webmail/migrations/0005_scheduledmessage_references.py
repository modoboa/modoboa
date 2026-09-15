from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("webmail", "0004_scheduledmessage_body_format"),
    ]

    operations = [
        migrations.AddField(
            model_name="scheduledmessage",
            name="references",
            field=models.TextField(blank=True, default=""),
        ),
    ]
