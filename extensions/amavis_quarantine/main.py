# -*- coding: utf-8 -*-

"""
"""
from django.conf.urls.defaults import *
from django.utils.translation import ugettext as _, ungettext
from django.core.urlresolvers import reverse
from modoboa.lib import events, parameters, static_url

def infos():
    return {
        "name" : "Amavis quarantine",
        "version" : "1.0",
        "description" : _("Simple amavis quarantine management tool")
        }

def init():
    events.register("UserMenuDisplay", menu)
    parameters.register_admin("MAX_MESSAGES_AGE", type="int", 
                              deflt=14,
                              help=_("Quarantine messages maximum age (in days) before deletion"))
    parameters.register_admin("AM_PDP_MODE", type="list", 
                              deflt="unix",
                              values=[("inet", "inet"), ("unix", "unix")],
                              help=_("Mode used to access the PDP server"))
    parameters.register_admin("AM_PDP_HOST", type="string", 
                              deflt="localhost", 
                              help=_("PDP server address (if inet mode)"))
    parameters.register_admin("AM_PDP_PORT", type="int", 
                              deflt=9998, 
                              help=_("PDP server port (if inet mode)"))
    parameters.register_admin("AM_PDP_SOCKET", type="string", 
                              deflt="/var/amavis/amavisd.sock",
                              help=_("Path to the PDP server socket (if unix mode)"))

def destroy():
    events.unregister("UserMenuDisplay", menu)
    parameters.unregister_app("amavis_quarantine")

def urls():
    return (r'^modoboa/quarantine/', 
            include('modoboa.extensions.amavis_quarantine.urls'))

def menu(**kwargs):
    import views

    if kwargs["target"] == "top_menu":
        return [
            {"name" : "quarantine",
             "label" : _("Quarantine"),
             "url" : reverse(views.index),
             "img" : static_url("pics/quarantine.png")}
            ]
    return []

