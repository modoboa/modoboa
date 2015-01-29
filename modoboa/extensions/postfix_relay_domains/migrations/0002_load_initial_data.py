# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from modoboa.core.extensions import exts_pool
from modoboa.lib.migration_tools import add_permissions_to_group

from ..modo_extension import RESELLERS_PERMISSIONS


def load_initial_data(apps, schema_editor):
    """Load initial data."""
    Service = apps.get_model("postfix_relay_domains", "Service")
    for service_name in ['relay', 'smtp']:
        Service.objects.get_or_create(name=service_name)

    if not exts_pool.is_extension_installed("modoboa.extensions.limits"):
        return

    Group = apps.get_model("auth", "Group")
    LimitsPool = apps.get_model("limits", "LimitsPool")
    Limit = apps.get_model("limits", "Limit")

    # Add new limits to existing pools. Set maxvalue to 0 because we
    # don't want to load the parameters module here...
    new_limits = ["relay_domains_limit", "relay_domain_aliases_limit"]
    for pool in LimitsPool.objects.all():
        for lname in new_limits:
            Limit.objects.create(name=lname, pool=pool, maxvalue=0)

    # Add new permissions to the Resellers group.
    grp = Group.objects.get(name='Resellers')
    add_permissions_to_group(apps, grp, RESELLERS_PERMISSIONS)


class Migration(migrations.Migration):

    dependencies = [
        ('postfix_relay_domains', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data)
    ]
