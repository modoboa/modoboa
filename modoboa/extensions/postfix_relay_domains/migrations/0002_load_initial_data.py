# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def load_initial_data(apps, schema_editor):
    """Load initial data."""
    Service = apps.get_model("postfix_relay_domains", "Service")
    for service_name in ['relay', 'smtp']:
        Service.objects.get_or_create(name=service_name)


class Migration(migrations.Migration):

    dependencies = [
        ('postfix_relay_domains', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data)
    ]
