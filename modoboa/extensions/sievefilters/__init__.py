# coding: utf-8
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse
from modoboa.lib import events, parameters
from modoboa.extensions import ModoExtension, exts_pool
from sievelib.managesieve import SUPPORTED_AUTH_MECHS

class SieveFilters(ModoExtension):
    name = "sievefilters"
    label = "Sieve filters"
    version = "1.0"
    description = ugettext_lazy("Plugin to easily create server-side filters")
    url = "sfilters"

    def load(self):
        parameters.register_app(uparams_opts=dict(needs_mailbox=True))
        
        parameters.register_admin("SERVER", type="string", 
                                  deflt="127.0.0.1",
                                  help=ugettext_lazy("Address of your MANAGESIEVE server"))
        parameters.register_admin("PORT", type="int", deflt="2000",
                                  help=ugettext_lazy("Listening port of your MANAGESIEVE server"))
        parameters.register_admin("STARTTLS", type="list_yesno", deflt="no",
                                  help=ugettext_lazy("Use the STARTTLS extension"))

        values = [('AUTO', 'auto')]
        for m in SUPPORTED_AUTH_MECHS:
            values += [(m, m.lower())]
        parameters.register_admin("AUTHENTICATION_MECH", type="list", deflt="auto",
                                  values=values,
                                  help=ugettext_lazy("Prefered authentication mechanism"))

        # User parameters
        parameters.register_user("EDITOR_MODE", type="list", deflt="raw",
                                 label=ugettext_lazy("Editor mode"),
                                 values=[("raw", "raw"), ("gui", "simplified")],
                                 help=ugettext_lazy("Select the mode you want the editor to work in"))
    
    def destroy(self):
        events.unregister("UserMenuDisplay", menu)
        parameters.unregister_app("sievefilters")

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
