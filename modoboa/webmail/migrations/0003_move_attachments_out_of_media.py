import os
import shutil

from django.conf import settings
from django.db import migrations, models

import modoboa.webmail.lib.attachments


def move_attachments_out_of_media(apps, schema_editor):
    """Move the files of existing scheduled messages out of MEDIA_ROOT."""
    MessageAttachment = apps.get_model("webmail", "MessageAttachment")
    legacy_dir = os.path.join(settings.MEDIA_ROOT, "webmail")
    target_dir = modoboa.webmail.lib.attachments.get_attachments_dir()
    for name in MessageAttachment.objects.values_list("file", flat=True):
        name = os.path.basename(name)
        source = os.path.join(legacy_dir, name)
        target = os.path.join(target_dir, name)
        if not os.path.isfile(source) or os.path.exists(target):
            continue
        os.makedirs(target_dir, mode=0o700, exist_ok=True)
        shutil.move(source, target)


class Migration(migrations.Migration):

    dependencies = [
        ("webmail", "0002_scheduledmessage_request_dsn_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="messageattachment",
            name="file",
            field=models.FileField(
                storage=modoboa.webmail.lib.attachments.WebmailAttachmentStorage(),
                upload_to="",
            ),
        ),
        migrations.RunPython(move_attachments_out_of_media, migrations.RunPython.noop),
    ]
