# coding: utf-8
"""
Amavis quarantine manager (SQL based)

"""
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse
from django.template import Template, Context
from modoboa.lib import events, parameters
from modoboa.extensions import ModoExtension, exts_pool

class Amavis(ModoExtension):
    name = "amavis"
    label = "Amavis frontend"
    version = "1.0"
    description = ugettext_lazy("Simple amavis management frontend")
    url = "quarantine"

    def init(self):
        """Init function
        
        Only run once, when the extension is enabled. We create records
        for existing mailboxes in order Amavis considers them local.
        """
        from modoboa.admin.models import Mailbox
        from models import Users
        
        for mb in Mailbox.objects.all():
            try:
                u = Users.objects.get(email=mb.full_address)
            except Users.DoesNotExist:
                u = Users()            
                u.email = mb.full_address
                u.fullname = mb.user.fullname
                u.local = "1"
                u.priority = 7
                u.policy_id = 1
                u.save()

    def load(self):
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
                                  help=ugettext_lazy("Mode used to access the PDP server"))
        parameters.register_admin("AM_PDP_HOST", type="string", 
                                  deflt="localhost", 
                                  help=ugettext_lazy("PDP server address (if inet mode)"))
        parameters.register_admin("AM_PDP_PORT", type="int", 
                                  deflt=9998, 
                                  help=ugettext_lazy("PDP server port (if inet mode)"))
        parameters.register_admin("AM_PDP_SOCKET", type="string", 
                                  deflt="/var/amavis/amavisd.sock",
                                  help=ugettext_lazy("Path to the PDP server socket (if unix mode)"))
        parameters.register_admin("CHECK_REQUESTS_INTERVAL", type="int",
                                  deflt=30,
                                  help=ugettext_lazy("Interval between two release requests checks"))
        parameters.register_admin("USER_CAN_RELEASE", type="list_yesno", deflt="no",
                                  help=ugettext_lazy("Allow users to directly release their messages"))
        parameters.register_admin("SELF_SERVICE", type="list_yesno", deflt="no",
                                  help=ugettext_lazy("Activate the 'self-service' mode"))
        parameters.register_admin("NOTIFICATIONS_SENDER", type="string", deflt="notification@modoboa.org",
                                  help=ugettext_lazy("The e-mail address used to send notitications"))
        
        parameters.register_user(
            "MESSAGES_PER_PAGE", type="int", deflt=40,
            label="Number of displayed emails per page",
            help=ugettext_lazy("Sets the maximum number of messages displayed in a page")
            )

        def destroy(self):
            events.unregister("UserMenuDisplay", menu)
            parameters.unregister_app("amavis")

exts_pool.register_extension(Amavis)

@events.observe("UserMenuDisplay")
def menu(target, user):
    from modoboa.lib.webutils import static_url

    if target == "top_menu":
        return [
            {"name" : "quarantine",
             "label" : _("Quarantine"),
             "url" : reverse('modoboa.extensions.amavis.views.index')}
            ]
    return []

@events.observe("DeleteDomain")
def on_delete_domain(domain):
    from models import Users

    try:
        u = Users.objects.get(email="@%s" % domain.name)
    except Users.DoesNotExist:
        return
    u.policy.delete()
    u.delete()

@events.observe("CreateMailbox")
def create_user_record(user, mailbox):
    from models import Users

    try:
        Users.objects.get(email=mailbox.full_address)
    except Users.DoesNotExist:
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
def remove_user_record(mailboxes):
    from models import Users
    from modoboa.admin.models import Mailbox

    if isinstance(mailboxes, Mailbox):
        mailboxes = [mailboxes]
    for mailbox in mailboxes:
        try:
            Users.objects.get(email=mailbox.full_address).delete()
        except Users.DoesNotExist:
            pass

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
                $link.html(data.requests + " " + "{{ text }}");
                $link.parent().removeClass('hidden');
            } else {
                $link.parent().addClass('hidden');
            }
        }
    });
});
</script>""")
    url = reverse("modoboa.extensions.amavis.views.nbrequests")
    interval = int(parameters.get_admin("CHECK_REQUESTS_INTERVAL")) * 1000
    return [tpl.render(Context(dict(url=url, interval=interval, text=_("pending requests"))))]

@events.observe("TopNotifications")
def display_requests(user):
    from lib import get_nb_requests

    if parameters.get_admin("USER_CAN_RELEASE") == "yes" \
            or user.group == "SimpleUsers":
        return []
    nbrequests = get_nb_requests(user)

    url = reverse("modoboa.extensions.amavis.views.index")
    url += "#listing/?viewrequests=1"
    tpl = Template('<div class="btn-group {{ css }}"><a id="nbrequests" href="{{ url }}" class="btn btn-danger">{{ label }}</a></div>')
    css = "hidden" if nbrequests == 0 else ""
    return [tpl.render(Context(dict(
                    label=_("%d pending requests" % nbrequests), url=url, css=css
                    )))]

@events.observe("ExtraDomainForm")
def extra_domain_form(user, domain):
    from forms import DomainPolicyForm

    if not user.has_perm("admin.view_domains"):
        return []
    return [
        dict(
            id="amavis", title=_("Content filter"), cls=DomainPolicyForm,
            formtpl="amavis/domain_content_filter.html"
            )
        ]

@events.observe("FillDomainInstances")
def fill_domain_instances(user, domain, instances):
    if not user.has_perm("admin.view_domains"):
        return
    instances["amavis"] = domain
