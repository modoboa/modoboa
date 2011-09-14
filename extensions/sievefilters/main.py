# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_noop as _, ugettext
from django.core.urlresolvers import reverse
from django.conf.urls.defaults import include
from modoboa.lib import events, parameters
from modoboa.lib.webutils import static_url
from sievelib.managesieve import SUPPORTED_AUTH_MECHS

def init():
    events.register("UserMenuDisplay", menu)
    events.register("UserLogout", userlogout)

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
        "description" : ugettext("Plugin to easily create server-side filters")
        }

def urls(prefix):
    return (r'^%ssfilters/' % prefix,
            include('modoboa.extensions.sievefilters.urls'))

def menu(**kwargs):
    import views

    if kwargs["target"] != "options_menu":
        return []
    return [
        {"name" : "sievefilters",
         "label" : ugettext("Message filters"),
         "url" : reverse(views.index),
         "img" : static_url("pics/filters.png")}
        ]

def userlogout(**kwargs):
    from lib import SieveClient

    if kwargs["request"].user.id == 1:
        return
    try:
        sc = SieveClient(user=kwargs["request"].user.username,
                         password=kwargs["request"].session["password"])
    except Exception, e:
        pass
    else:
        sc.logout()
