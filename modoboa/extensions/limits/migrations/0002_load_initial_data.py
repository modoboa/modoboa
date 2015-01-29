# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from modoboa.core.extensions import exts_pool
from modoboa.lib.migration_tools import add_permissions_to_group
from modoboa.extensions.limits.midels import LimitTemplates


def load_initial_data(apps, schema_editor):
    """Load initial data."""
    Group = apps.get_model("auth", "Group")
    User = apps.get_model("core", "User")
    LimitsPool = apps.get_model("limits", "LimitsPool")
    Limit = apps.get_model("limits", "Limit")

    dagrp = Group.objects.get(name="DomainAdmins")
    grp = Group(name="Resellers")
    grp.save()
    grp.permissions.add(*dagrp.permissions.all())
    add_permissions_to_group(
        apps, grp, [("admin", "domain", "view_domains"),
                    ("admin", "domain", "add_domain"),
                    ("admin", "domain", "change_domain"),
                    ("admin", "domain", "delete_domain")]
    )
    if exts_pool.is_extension_installed(
            "modoboa.extensions.postfix_relay_domains"):
        from modoboa.extensions.postfix_relay_domains.modo_extension \
            import RESELLERS_PERMISSIONS
        add_permissions_to_group(apps, grp, RESELLERS_PERMISSIONS)

    for user in User.objects.filter(groups__name="DomainAdmins"):
        pool, created = LimitsPool.objects.get_or_create(user=user)
        for tpl in LimitTemplates().templates():
            Limit.objects.create(name=tpl[0], pool=pool, maxvalue=0)


class Migration(migrations.Migration):

    dependencies = [
        ('limits', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data)
    ]
