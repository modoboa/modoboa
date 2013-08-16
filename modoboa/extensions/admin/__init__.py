# coding: utf-8
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.core.extensions import ModoExtension, exts_pool
from modoboa.lib import parameters, events


class AdminConsole(ModoExtension):
    name = "admin"
    label = ugettext_lazy("Administration console")
    version = "1.0"
    description = ugettext_lazy("Web based console to manage domains, accounts and aliases")
    always_active = True

    def load(self):
        from app_settings import AdminParametersForm
        parameters.register(AdminParametersForm, ugettext_lazy("Administration"))

    def destroy(self):
        parameters.unregister()

exts_pool.register_extension(AdminConsole, show=False)
