# coding: utf-8
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.extensions import ModoExtension, exts_pool
from modoboa.lib import parameters, events


class AdminConsole(ModoExtension):
    name = "admin"
    label = ugettext_lazy("Administration console")
    version = "1.0"
    description = ugettext_lazy("Web based console to manage domains, accounts and aliases")
    always_active = True

    def load(self):
        from app_settings import GeneralParametersForm
        parameters.register(GeneralParametersForm, _("General"))

    def destroy(self):
        parameters.unregister()

exts_pool.register_extension(AdminConsole, show=False)


@events.observe("ExtDisabled")
def unset_default_topredirection(extension):
    """
    Simple callback to change the default redirection if the
    corresponding extension is being disabled.
    """
    topredirection = parameters.get_admin("DEFAULT_TOP_REDIRECTION")
    if topredirection == extension.name:
        parameters.save_admin("DEFAULT_TOP_REDIRECTION", "userprefs")
