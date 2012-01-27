# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_noop as _, ugettext
from django.core.urlresolvers import reverse
from modoboa.lib import events, parameters
from modoboa.lib.webutils import static_url
from sievelib.managesieve import SUPPORTED_AUTH_MECHS

baseurl = "sfilters"

def load():
    parameters.register_admin("SERVER", type="string", 
                              deflt="127.0.0.1",
                              help=_("Address of your MANAGESIEVE server"))
    parameters.register_admin("PORT", type="int", deflt="2000",
                              help=_("Listening port of your MANAGESIEVE server"))
    parameters.register_admin("STARTTLS", type="list_yesno", deflt="no",
                              help=_("Use the STARTTLS extension"))

    values = [('AUTO', 'auto')]
    for m in SUPPORTED_AUTH_MECHS:
        values += [(m, m.lower())]
    parameters.register_admin("AUTHENTICATION_MECH", type="list", deflt="auto",
                              values=values,
                              help=_("Prefered authentication mechanism"))

    # User parameters
    parameters.register_user("EDITOR_MODE", type="list", deflt="raw",
                             label=_("Editor mode"),
                             values=[("raw", "raw"), ("gui", "simplified")],
                             help=_("Select the mode you want the editor to work in"))
    
def destroy():
    events.unregister("UserMenuDisplay", menu)
    parameters.unregister_app("sievefilters")

def infos():
    return {
        "name" : "Sieve filters",
        "version" : "1.0",
        "description" : ugettext("Plugin to easily create server-side filters"),
        "url" : "sfilters"
        }

@events.observe("UserMenuDisplay")
def menu(target, user):
    import views

    if target != "options_menu":
        return []
    if not user.has_mailbox:
        return []
    return [
        {"name" : "sievefilters",
         "label" : ugettext("Message filters"),
         "url" : reverse(views.index),
         "img" : static_url("pics/filters.png")}
        ]

@events.observe("Userlogout")
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
