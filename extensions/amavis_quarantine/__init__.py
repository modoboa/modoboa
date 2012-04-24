# coding: utf-8
"""
Amavis quarantine manager (SQL based)


"""
from django.utils.translation import ugettext_noop as _, ugettext
from django.core.urlresolvers import reverse
from django.template import Template, Context
from modoboa.lib import events, parameters

baseurl = "quarantine"

def infos():
    return {
        "name" : "Amavis quarantine",
        "version" : "1.0",
        "description" : ugettext("Simple amavis quarantine management tool"),
        "url" : "quarantine"
        }

def load():
    parameters.register_admin(
        "MAX_MESSAGES_AGE", type="int", 
        deflt=14,
        help=_("Quarantine messages maximum age (in days) before deletion")
        )
    parameters.register_admin(
        "RELEASED_MSGS_CLEANUP", type="list_yesno", deflt="no",
        help=_("Remove messages marked as released while cleaning up the database")
        )
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
                              deflt=_("/var/amavis/amavisd.sock"),
                              help=_("Path to the PDP server socket (if unix mode)"))
    parameters.register_admin("CHECK_REQUESTS_INTERVAL", type="int",
                              deflt=30,
                              help=_("Interval between two release requests checks"))
    parameters.register_admin("USER_CAN_RELEASE", type="list_yesno", deflt="no",
                              help=_("Allow users to directly release their messages"))
    parameters.register_admin("SELF_SERVICE", type="list_yesno", deflt="no",
                              help=_("Activate the 'self-service' mode"))

    parameters.register_user(
        "MESSAGES_PER_PAGE", type="int", deflt=40,
        label="Number of displayed emails per page",
        help=_("Sets the maximum number of messages displayed in a page")
        )

def destroy():
    events.unregister("UserMenuDisplay", menu)
    parameters.unregister_app("amavis_quarantine")

@events.observe("UserMenuDisplay")
def menu(target, user):
    from modoboa.lib.webutils import static_url

    if target == "top_menu":
        return [
            {"name" : "quarantine",
             "label" : ugettext("Quarantine"),
             "url" : reverse('modoboa.extensions.amavis_quarantine.views.index'),
             "img" : static_url("pics/quarantine.png")}
            ]
    return []

@events.observe("CreateMailbox")
def create_user_record(user, mailbox):
    from models import Users

    u = Users()
    u.email = mailbox.full_address
    u.fullname = mailbox.user.fullname
    u.local = "1"
    u.priority = 7
    u.policy_id = 1
    u.save()

@events.observe("ModifyMailbox")
def modify_user_record(mailbox, oldmailbox):
    if mailbox.full_address == oldmailbox.full_address:
        return
    u = Users.objects.get(email=oldmailbox.full_address)
    u.email = mailbox.full_address
    u.save()

@events.observe("DeleteMailbox")
def remove_user_record(mailbox):
    from models import Users

    Users.objects.get(email=mailbox.full_address).delete()

@events.observe("GetStaticContent")
def extra_static_content(user):
    if parameters.get_admin("USER_CAN_RELEASE") == "yes" \
            or user.group == "SimpleUsers":
        return []

    tpl = Template("""<script type="text/javascript">
$(document).ready(function() {
    var poller = new Poller("{{ url }}", {
        interval: {{ interval }},
        success_cb: function(data) {
            var $link = $("#nbrequests");
            if (data.requests > 0) {
                $link.html(data.requests + " " + gettext("pending requests"));
                $link.parent().removeClass('hidden');
            } else {
                $link.parent().addClass('hidden');
            }
        }
    });
});
</script>""")
    url = reverse("modoboa.extensions.amavis_quarantine.views.nbrequests")
    interval = int(parameters.get_admin("CHECK_REQUESTS_INTERVAL")) * 1000
    return [tpl.render(Context(dict(url=url, interval=interval)))]

@events.observe("TopNotifications")
def display_requests(user):
    from lib import get_nb_requests

    if parameters.get_admin("USER_CAN_RELEASE") == "yes" \
            or user.group == "SimpleUsers":
        return []
    nbrequests = get_nb_requests(user)

    url = reverse("modoboa.extensions.amavis_quarantine.views.index")
    url += "#listing/?viewrequests=1"
    tpl = Template('<div class="btn-group {{ css }}"><a id="nbrequests" href="{{ url }}" class="btn btn-danger">{{ label }}</a></div>')
    css = "hidden" if nbrequests == 0 else ""
    return [tpl.render(Context(dict(
                    label=_("%d pending requests" % nbrequests), url=url, css=css
                    )))]
