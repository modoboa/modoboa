# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from modoboa.core.extensions import exts_pool


def load_initial_data(apps, schema_editor):
    """Load initial data."""
    Service = apps.get_model("postfix_relay_domains", "Service")
    for service_name in ['relay', 'smtp']:
        Service.objects.get_or_create(name=service_name)

    if not exts_pool.is_extension_installed("modoboa.extensions.limits"):
        return

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    RelayDomain = apps.get_model("postfix_relay_domains", "RelayDomain")
    RelayDomainAlias = apps.get_model(
        "postfix_relay_domains", "RelayDomainAlias")
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
    for model in [RelayDomain, RelayDomainAlias, Service]:
        ct = ContentType.objects.get_for_model(model)
        name = model.__name__.lower()
        for action in ['add', 'change', 'delete']:
            grp.permissions.add(
                Permission.objects.get(
                    content_type=ct, codename='%s_%s' % (action, name)
                )
            )
    grp.save()



class Migration(migrations.Migration):

    dependencies = [
        ('postfix_relay_domains', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data)
    ]
