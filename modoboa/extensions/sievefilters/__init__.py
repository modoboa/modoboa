# coding: utf-8
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse
from modoboa.lib import events, parameters
from modoboa.core.extensions import ModoExtension, exts_pool


class SieveFilters(ModoExtension):
    name = "sievefilters"
    label = "Sieve filters"
    version = "1.0"
    description = ugettext_lazy("Plugin to easily create server-side filters")
    url = "sfilters"

    def load(self):
        from .app_settings import ParametersForm, UserSettings
        parameters.register(ParametersForm, ugettext_lazy("Sieve filters"))
        parameters.register(UserSettings, ugettext_lazy("Message filters"))

    def destroy(self):
        events.unregister("UserMenuDisplay", menu)
        parameters.unregister()

exts_pool.register_extension(SieveFilters)


@events.observe("UserMenuDisplay")
def menu(target, user):
    if target != "options_menu":
        return []
    if not user.mailbox_set.count():
        return []
    return [
        {"name": "sievefilters",
         "label": _("Message filters"),
         "url": reverse("modoboa.extensions.sievefilters.views.index"),
         "img": "icon-check"}
    ]


@events.observe("UserLogout")
def userlogout(request):
    from .lib import SieveClient

    if not request.user.mailbox_set.count():
        return
    try:
        sc = SieveClient(user=request.user.username,
                         password=request.session["password"])
    except Exception:
        pass
    else:
        sc.logout()
