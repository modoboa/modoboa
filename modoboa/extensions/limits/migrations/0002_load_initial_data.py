# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from modoboa.extensions.limits.models import LimitTemplates


def load_initial_data(apps, schema_editor):
    """Load initial data."""
    User = apps.get_model("core", "User")
    LimitsPool = apps.get_model("limits", "LimitsPool")
    Limit = apps.get_model("limits", "Limit")

    for user in User.objects.filter(groups__name="DomainAdmins"):
        pool, created = LimitsPool.objects.get_or_create(user=user)
        for tpl in LimitTemplates().templates:
            Limit.objects.create(name=tpl[0], pool=pool, maxvalue=0)


class Migration(migrations.Migration):

    dependencies = [
        ('limits', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data)
    ]
