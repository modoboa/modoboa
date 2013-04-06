# coding: utf-8
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse
from modoboa.lib import events, parameters
from modoboa.extensions import ModoExtension, exts_pool


class SieveFilters(ModoExtension):
    name = "sievefilters"
    label = "Sieve filters"
    version = "1.0"
    description = ugettext_lazy("Plugin to easily create server-side filters")
    url = "sfilters"

    def load(self):
        from app_settings import ParametersForm, UserSettings
        parameters.register(ParametersForm, _("Sieve filters"))
        parameters.register(UserSettings, _("Message filters"))

    def destroy(self):
        events.unregister("UserMenuDisplay", menu)
        parameters.unregister()

exts_pool.register_extension(SieveFilters)

@events.observe("UserMenuDisplay")
def menu(target, user):
    import views

    if target != "options_menu":
        return []
    if not user.has_mailbox:
        return []
    return [
        {"name" : "sievefilters",
         "label" : _("Message filters"),
         "url" : reverse(views.index),
         "img" : "icon-check"}
        ]

@events.observe("UserLogout")
def userlogout(request):
    from lib import SieveClient

    if not request.user.has_mailbox:
        return
    try:
        sc = SieveClient(user=request.user.username,
                         password=request.session["password"])
    except Exception, e:
        pass
    else:
        sc.logout()
