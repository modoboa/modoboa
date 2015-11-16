"""A management command to load Modoboa initial data:

* Create a default super admin if none exists
* Create groups and permissions

"""

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from modoboa.admin.app_settings import load_admin_settings
from modoboa.core import load_core_settings, PERMISSIONS
from modoboa.core.extensions import exts_pool
from modoboa.core.models import User, ObjectAccess
from modoboa.lib.cryptutils import random_key
from modoboa.lib import events
from modoboa.lib import models as lib_models
from modoboa.lib.permissions import add_permissions_to_group
from modoboa.limits.app_settings import load_limits_settings
import modoboa.relaydomains.models as relay_models


class Command(BaseCommand):

    """Command defintion."""

    help = "Load Modoboa initial data"

    def handle(self, *args, **options):
        """Command entry point."""
        load_core_settings()
        load_admin_settings()
        load_limits_settings()

        if not User.objects.filter(is_superuser=True).count():
            admin = User(username="admin", is_superuser=True)
            admin.set_password("password")
            admin.save()
            ObjectAccess.objects.create(
                user=admin, content_object=admin, is_owner=True)

        param_name = "core.SECRET_KEY"
        qset = lib_models.Parameter.objects.filter(name=param_name)
        if not qset.exists():
            lib_models.Parameter.objects.create(
                name=param_name, value=random_key())

        for service_name in ['relay', 'smtp']:
            relay_models.Service.objects.get_or_create(name=service_name)

        exts_pool.load_all()

        superadmin = User.objects.filter(is_superuser=True).first()
        groups = PERMISSIONS.keys() + [
            role[0] for role
            in events.raiseQueryEvent("GetExtraRoles", superadmin, None)
        ]
        for groupname in groups:
            group, created = Group.objects.get_or_create(name=groupname)
            permissions = (
                PERMISSIONS.get(groupname, []) +
                events.raiseQueryEvent("GetExtraRolePermissions", groupname)
            )
            if not permissions:
                continue
            add_permissions_to_group(group, permissions)

        for extname in exts_pool.extensions.keys():
            extension = exts_pool.get_extension(extname)
            extension.load_initial_data()
            events.raiseEvent("InitialDataLoaded", extname)
