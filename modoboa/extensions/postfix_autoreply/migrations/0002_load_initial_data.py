# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from modoboa.extensions.postfix_autoreply.general_callbacks import (
    onDomainCreated, onMailboxCreated
)


def load_initial_data(apps, schema_editor):
    """Load initial data."""
    Domain = apps.get_model("admin", "Domain")
    Transport = apps.get_model("postfix_autoreply", "Transport")
    Alias = apps.get_model("postfix_autoreply", "Alias")

    for dom in Domain.objects.all():
        try:
            Transport.objects.get(domain="autoreply.%s" % dom.name)
        except Transport.DoesNotExist:
            onDomainCreated(None, dom)
        else:
            continue

        for mb in dom.mailbox_set.all():
            try:
                Alias.objects.get(full_address=mb.full_address)
            except Alias.DoesNotExist:
                onMailboxCreated(None, mb)


class Migration(migrations.Migration):

    dependencies = [
        ('postfix_autoreply', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data)
    ]
