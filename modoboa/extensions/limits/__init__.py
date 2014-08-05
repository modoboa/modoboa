# coding: utf-8

"""
The *limits* extension
----------------------
"""
import sys
from django.contrib.auth.models import Permission, Group
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy
from modoboa.lib import events, parameters
from modoboa.lib.permissions import add_permissions_to_group
from modoboa.core.extensions import ModoExtension, exts_pool

levents = [
    'GetExtraLimitTemplates'
]


class Limits(ModoExtension):
    name = "limits"
    label = "Limits"
    version = "1.0"
    description = ugettext_lazy(
        "Per administrator resources to limit the number of objects "
        "they can create"
    )

    def init(self):
        from modoboa.core.models import User
        from modoboa.extensions.admin.models import Domain

        ct = ContentType.objects.get(app_label="admin", model="domain")
        dagrp = Group.objects.get(name="DomainAdmins")

        grp = Group(name="Resellers")
        grp.save()
        grp.permissions.add(*dagrp.permissions.all())

        ct = ContentType.objects.get_for_model(Domain)
        add_permissions_to_group(
            "Resellers", [("admin", "domain", "view_domains"),
                          ("admin", "domain", "add_domain"),
                          ("admin", "domain", "change_domain"),
                          ("admin", "domain", "delete_domain")]
        )

        for user in User.objects.filter(groups__name='DomainAdmins'):
            try:
                controls.create_pool(user)
            except IntegrityError:
                pass

    def load(self):
        from modoboa.extensions.limits.app_settings import ParametersForm
        from modoboa.extensions.limits import controls

        parameters.register(ParametersForm, ugettext_lazy("Limits"))
        events.declare(levents)
        from modoboa.extensions.limits import general_callbacks
        if 'modoboa.extensions.limits.general_callbacks' in sys.modules:
            reload(general_callbacks)

    def destroy(self):
        events.unregister_extension()
        parameters.unregister()
        Group.objects.get(name="Resellers").delete()

exts_pool.register_extension(Limits)
