# coding: utf-8
"""
Amavis management frontend.

Provides:

* SQL quarantine management
* Per-domain settings

"""
import sys
from django.utils.translation import ugettext_lazy
from modoboa.lib import events, parameters
from modoboa.core.extensions import ModoExtension, exts_pool


class Amavis(ModoExtension):
    name = "amavis"
    label = "Amavis frontend"
    version = "1.0"
    description = ugettext_lazy("Simple amavis management frontend")
    url = "quarantine"
    available_for_topredirection = True

    def init(self):
        """Init function

        Only run once, when the extension is enabled. We create records
        for existing domains to let Amavis consider them local.
        """
        from modoboa.extensions.admin.models import Domain
        from .models import Users, Policy

        for dom in Domain.objects.all():
            try:
                Users.objects.get(email="@%s" % dom.name)
            except Users.DoesNotExist:
                p = Policy.objects.create(policy_name=dom.name)
                Users.objects.create(email="@%s" % dom.name, fullname=dom.name,
                                     priority=7, policy=p)

    def load(self):
        from .app_settings import ParametersForm, UserSettings

        parameters.register(ParametersForm, "Amavis")
        parameters.register(UserSettings, ugettext_lazy("Quarantine"))
        from modoboa.extensions.amavis import general_callbacks
        if 'modoboa.extensions.amavis.general_callbacks' in sys.modules:
            reload(general_callbacks)

    def destroy(self):
        events.unregister_extension()
        parameters.unregister()

exts_pool.register_extension(Amavis)
