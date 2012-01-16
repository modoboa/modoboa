# coding: utf-8

"""
The *limits* extension
----------------------


"""
from django.utils.translation import ugettext_noop as _, ugettext
from django.core.urlresolvers import reverse
from django.conf.urls.defaults import include
from modoboa.lib import events, parameters
from modoboa.lib.webutils import static_url
from controls import *

baseurl = "limits"

def init():
    events.register("AdminMenuDisplay", menu)
    events.register("CanCreateDomain", check_domains_limit)
    events.register("CreateDomain", associate_domain_to_reseller)
    events.register("GetUserDomains", get_reseller_domains)

def destroy():
    events.unregister("AdminMenuDisplay", menu)

def infos():
    return {
        "name" : "Limits",
        "version" : "1.0",
        "description" : ugettext("Limits for objects creation"),
        "url" : baseurl
        }

def menu(target, user):
    import views

    if target != "top_menu":
        return []
    if not user.is_superuser:
        return []
    return [
        {"name" : "resellers",
         "label" : _("Resellers"),
         "url" : reverse(views.resellers),
         "img" : static_url("pics/resellers.png")}
        ]

def urls(prefix):
    return (r'^%s%s/' % (prefix, baseurl),
            include('modoboa.extensions.limits.urls'))
