# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from modoboa.core.extensions import exts_pool


def load_initial_data(apps, schema_editor):
    """Load initial data."""
    Domain = apps.get_model("admin", "Domain")
    Policy = apps.get_model("amavis", "Policy")
    Users = apps.get_model("amavis", "Users")

    for dom in Domain.objects.all():
        name = "@{0}".format(dom.name)
        policy, created = Policy.objects.get_or_create(policy_name=name[:32])
        Users.objects.get_or_create(
            email=name, fullname=name, priority=7, policy=policy)
        for dalias in dom.domainalias_set.all():
            name = "@{0}".format(dalias.name)
            Users.objects.get_or_create(
                email=name, fullname=name, priority=7, policy=policy)

    if not exts_pool.is_extension_installed(
            "modoboa.extensions.postfix_relay_domains"):
        return

    RelayDomain = apps.get_model("postfix_relay_domains", "RelayDomain")

    for dom in RelayDomain.objects.all():
        name = "@{0}".format(dom.name)
        policy, created = Policy.objects.get_or_create(policy_name=name[:32])
        Users.objects.get_or_create(
            email=name, fullname=name, priority=7, policy=policy)
        for rdalias in dom.relaydomainalias_set.all():
            name = "@{0}".format(rdalias.name)
            Users.objects.get_or_create(
                email=name, fullname=name, priority=7, policy=policy)



class Migration(migrations.Migration):

    dependencies = [
        ('amavis', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data)
    ]
