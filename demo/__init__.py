# coding: utf-8
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_noop as _
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

events.register("UserMenuDisplay", menu)
