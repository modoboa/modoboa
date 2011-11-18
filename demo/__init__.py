# coding: utf-8
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_noop as _
from django.template.loader import render_to_string
from modoboa.lib import events
from modoboa.lib.webutils import static_url

def menu(**kwargs):
    import views

    if kwargs["target"] != "top_menu_middle":
        return []
    return [
        {"name"  : "demo",
         "label" : _("Test messages"),
         "img" : static_url("pics/demo.png"),
         "class" : "topdropdown",
         "menu"  : [
                {"name"  : "sendvirus",
                 "label" :  _("Send virus"),
                 "img" : static_url("pics/send-receive.png"),
                 "url"   : reverse(views.send_virus)},
                {"name"  : "sendspam",
                 "label" :  _("Send spam"),
                 "img" : static_url("pics/send-receive.png"),
                 "url"   : reverse(views.send_spam)}
                ]
         }
        ]

def announcement(**kwargs):
    if kwargs["target"] == "loginpage":
        txt = render_to_string("demo/login_announcement.html")
        return [txt]
    return ""

if 'modoboa.demo' in settings.INSTALLED_APPS:
    events.register("UserMenuDisplay", menu)
    events.register("GetAnnouncement", announcement)
