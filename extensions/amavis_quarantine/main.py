# -*- coding: utf-8 -*-

"""
"""
from django.conf.urls.defaults import *
from django.utils.translation import ugettext as _, ungettext
from django.core.urlresolvers import reverse
from mailng.lib import events, parameters

def infos():
    return {
        "name" : "Amavis quarantine",
        "version" : "1.0",
        "description" : _("Simple amavis quarantine management tool")
        }

def init():
    events.register("UserMenuDisplay", menu)
    parameters.register("amavis_quarantine", "MAX_MESSAGES_AGE", "int", 14,
                        help=_("Quarantine messages maximum age (in days) before deletion"))
    parameters.register("amavis_quarantine", "AM_PDP_MODE", "list", "unix",
                        values=[("inet", "inet"), ("unix", "unix")],
                        help="")
    parameters.register("amavis_quarantine", "AM_PDP_HOST", "string", "localhost",
                        help="")
    parameters.register("amavis_quarantine", "AM_PDP_PORT", "int", 9998,
                        help="")
    parameters.register("amavis_quarantine", "AM_PDP_SOCKET", "string", 
                        "/var/amavis/amavisd.sock",
                        help="")

def destroy():
    events.unregister("UserMenuDisplay", menu)
    parameters.unregister_app("amavis_quarantine")

def urls():
    return (r'^mailng/quarantine/', 
            include('mailng.extensions.amavis_quarantine.urls'))

def menu(**kwargs):
    import views

    if kwargs["target"] == "user_menu_box":
        return [
            {"name" : "quarantine",
             "label" : _("Quarantine"),
             "url" : reverse(views.index, urlconf='mailng.extensions.amavis_quarantine.exturls'),
             "img" : "/static/pics/quarantine.png"}
            ]
    return []

