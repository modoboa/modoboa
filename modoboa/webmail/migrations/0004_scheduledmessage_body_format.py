from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("webmail", "0003_move_attachments_out_of_media"),
    ]

    operations = [
        migrations.AddField(
            model_name="scheduledmessage",
            name="body_format",
            field=models.CharField(
                blank=True,
                choices=[("plain", "text"), ("html", "html")],
                default="",
                max_length=5,
            ),
        ),
    ]
