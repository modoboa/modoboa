# coding: utf-8
"""
Amavis management frontend.

Provides:

* SQL quarantine management
* Per-domain settings

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
        for existing domains to let Amavis consider them local.
        """
        from modoboa.admin.models import Domain
        from models import Users, Policy

        for dom in Domain.objects.all():
            try:
                u = Users.objects.get(email="@%s" % dom.name)
            except Users.DoesNotExist:
                p = Policy.objects.create(policy_name=dom.name)
                Users.objects.create(email="@%s" % dom.name, fullname=dom.name,
                                     priority=7, policy=p)

    def load(self):
        from app_settings import ParametersForm, UserSettings
        parameters.register(ParametersForm, "Amavis")
        parameters.register(UserSettings, _("Quarantine"))
       
    def destroy(self):
        events.unregister("UserMenuDisplay", menu)
        parameters.unregister()

exts_pool.register_extension(Amavis)


@events.observe("UserMenuDisplay")
def menu(target, user):
    from modoboa.lib.webutils import static_url

    if target == "top_menu":
        return [
            {"name": "quarantine",
             "label": _("Quarantine"),
             "url": reverse('modoboa.extensions.amavis.views.index')}
            ]
    return []


@events.observe("CreateDomain")
def on_create_domain(user, domain):
    from models import Users, Policy
    p = Policy.objects.create(policy_name=domain.name)
    Users.objects.create(email="@%s" % domain.name, fullname=domain.name,
                         priority=7, policy=p)


@events.observe("DomainModified")
def on_domain_modified(domain):
    if domain.oldname != domain.name:
        from models import Users
        u = Users.objects.get(email="@%s" % domain.oldname)
        u.email = "@%s" % domain.name
        u.fullname = domain.name
        u.policy.policy_name = domain.name
        u.policy.save()
        u.save()


@events.observe("DeleteDomain")
def on_delete_domain(domain):
    from models import Users

    try:
        u = Users.objects.get(email="@%s" % domain.name)
    except Users.DoesNotExist:
        return
    u.policy.delete()
    u.delete()


@events.observe("GetStaticContent")
def extra_static_content(user):
    if user.group == "SimpleUsers":
        return []

    tpl = Template("""<script type="text/javascript">
$(document).ready(function() {
    {% if user_can_release == "no" %}var poller = new Poller("{{ url }}", {
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
    });{% endif %}

    $(document).bind('domform_init', function() {
        activate_widget.call($('#id_spam_subject_tag2_act'));
    });
});
</script>""")

    return [tpl.render(
        Context(dict(
            url=reverse("modoboa.extensions.amavis.views.nbrequests"),
            interval=int(parameters.get_admin("CHECK_REQUESTS_INTERVAL")) * 1000,
            text=_("pending requests"),
            user_can_release=parameters.get_admin("USER_CAN_RELEASE")
        ))
    )]


@events.observe("TopNotifications")
def display_requests(user):
    from sql_listing import get_wrapper

    if parameters.get_admin("USER_CAN_RELEASE") == "yes" \
            or user.group == "SimpleUsers":
        return []
    nbrequests = get_wrapper().get_pending_requests(user)

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
