# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def rename_content_types(apps, schema_editor):
    """Rename old content types if necessary."""
    ContentType = apps.get_model("contenttypes", "ContentType")
    for ct in ContentType.objects.filter(app_label="admin"):
        try:
            old_ct = ContentType.objects.get(
                app_label="modoboa_admin", model=ct.model)
        except ContentType.DoesNotExist:
            continue
        old_ct.app_label = "admin"
        ct.delete()
        old_ct.save()


class Migration(migrations.Migration):

    dependencies = [
        ('admin', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(rename_content_types),
    ]
