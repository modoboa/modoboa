# coding: utf-8
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from modoboa.lib import events
from modoboa.lib.webutils import static_url

@events.observe("UserMenuDisplay")
def menu(target, user):
    if target != "top_menu_middle":
        return []
    if not user.has_mailbox:
        return []
    return [
        {"name"  : "demo",
         "label" : _("Test messages"),
         "img" : static_url("pics/demo.png"),
         "class" : "topdropdown",
         "menu"  : [
                {"name"  : "sendvirus",
                 "label" :  _("Send virus"),
                 "url"   : reverse("modoboa.demo.views.send_virus")},
                {"name"  : "sendspam",
                 "label" :  _("Send spam"),
                 "url"   : reverse("modoboa.demo.views.send_spam")}
                ]
         }
        ]

@events.observe("GetAnnouncement")
def announcement(target):
    if target == "loginpage":
        txt = render_to_string("demo/login_announcement.html")
        return [txt]
    return ""

@events.observe("PasswordChange")
def password_change(user):
    return [user.id == 1]

@events.observe("GetStaticContent")
def get_static_content(user):
    if not user.has_mailbox:
        return []
    return """<script type="text/javascript">
$(document).ready(function() {
    $(document).on('click', 'a[name=sendspam]', simple_ajax_request);
    $(document).on('click', 'a[name=sendvirus]', simple_ajax_request);
});
</script>"""
