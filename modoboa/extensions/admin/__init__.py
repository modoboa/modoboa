# coding: utf-8
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse
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


@events.observe("AdminMenuDisplay")
def menu(target, user):
    if target != "top_menu":
        print "rien"
        return []
    entries = []
    if user.has_perm("admin.view_domains"):
        entries += [
            {"name" : "domains",
             "url" : reverse("modoboa.extensions.admin.views.domain.domains"),
             "label" : _("Domains")}
        ]
    if user.has_perm("admin.add_user") or user.has_perm("admin.add_alias"):
        entries += [
            {"name" : "identities",
             "url" : reverse("modoboa.extensions.admin.views.identity.identities"),
             "label" : _("Identities")},
        ]
    print entries
    return entries
