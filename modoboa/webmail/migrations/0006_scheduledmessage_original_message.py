from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("webmail", "0005_scheduledmessage_references"),
    ]

    operations = [
        migrations.AddField(
            model_name="scheduledmessage",
            name="original_action",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
        migrations.AddField(
            model_name="scheduledmessage",
            name="original_mailbox",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="scheduledmessage",
            name="original_mailid",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
