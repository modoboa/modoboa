# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def rename_and_clean(apps, schema_editor):
    """Rename old content types if necessary, remove permissions."""
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

    # Remove DomainAlias permissions from DomainAdmins group
    Group = apps.get_model("auth", "Group")
    try:
        group = Group.objects.get(name="DomainAdmins")
    except Group.DoesNotExist:
        return
    Permission = apps.get_model("auth", "Permission")
    ct = ContentType.objects.get(app_label="admin", model="domainalias")
    for permission in Permission.objects.filter(content_type=ct):
        group.permissions.remove(permission)


class Migration(migrations.Migration):

    dependencies = [
        ('admin', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(rename_and_clean),
    ]
