# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def move_aliases(apps, schema_editor):
    """Move exising aliases to the main table."""
    OldAlias = apps.get_model("postfix_autoreply", "Alias")
    Alias = apps.get_model("admin", "Alias")
    AliasRecipient = apps.get_model("admin", "AliasRecipient")
    try:
        ObjectDates = apps.get_model("admin", "ObjectDates")
    except LookupError:
        ObjectDates = None
    to_create = []
    for old_alias in OldAlias.objects.all():
        values = {"address": old_alias.full_address, "internal": True}
        try:
            alias = Alias.objects.get(**values)
        except Alias.DoesNotExist:
            if ObjectDates:
                values["dates"] = ObjectDates.objects.create()
            alias = Alias.objects.create(**values)
        to_create.append(
            AliasRecipient(address=old_alias.autoreply_address, alias=alias)
        )
    AliasRecipient.objects.bulk_create(to_create)


class Migration(migrations.Migration):

    dependencies = [
        ("postfix_autoreply", "0002_auto_20150728_1236"),
    ]

    operations = [migrations.RunPython(move_aliases)]
