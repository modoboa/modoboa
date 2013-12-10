from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.template import Template, Context
from modoboa.lib import events, parameters
from modoboa.extensions.admin.models import DomainAlias
from modoboa.extensions.amavis.lib import (
    create_user_and_policy, update_user_and_policy, delete_user_and_policy,
    create_user_and_use_policy, delete_user
)


@events.observe("UserMenuDisplay")
def menu(target, user):
    if target == "top_menu":
        return [
            {"name": "quarantine",
             "label": _("Quarantine"),
             "url": reverse('modoboa.extensions.amavis.views.index')}
        ]
    return []


@events.observe("DomainCreated")
def on_domain_created(user, domain):
    create_user_and_policy(domain.name)


@events.observe("DomainModified")
def on_domain_modified(domain):
    update_user_and_policy(domain.oldname, domain.name)


@events.observe("DomainDeleted")
def on_domain_deleted(domain):
    delete_user_and_policy(domain.name)


@events.observe("DomainAliasCreated")
def on_domain_alias_created(user, domainalias):
    create_user_and_use_policy(domainalias.name, domainalias.target.name)


@events.observe("DomainAliasDeleted")
def on_domain_alias_deleted(domainaliases):
    if isinstance(domainaliases, DomainAlias):
        domainaliases = [domainaliases]
    for domainalias in domainaliases:
        delete_user(domainalias.name)


@events.observe("GetStaticContent")
def extra_static_content(caller, user):
    if user.group == "SimpleUsers":
        return []

    if caller == 'top' and parameters.get_admin("USER_CAN_RELEASE") == 'no':
        tpl = Template("""<script type="text/javascript">
$(document).ready(function() {
    var poller = new Poller("{{ url }}", {
        interval: {{ interval }},
        success_cb: function(data) {
            var $link = $("#nbrequests");
            var $maincounter = $("#alerts-counter");

            if (data.requests > 0) {
                $maincounter.html(data.requests);
                $link.children("span").html(data.requests);
                $maincounter.closest('div').removeClass('hidden');
            } else {
                $maincounter.closest('div').addClass('hidden');
            }
        }
    });
});
</script>
""")
        return [tpl.render(
            Context({
                'url': reverse("modoboa.extensions.amavis.views.nbrequests"),
                'interval': int(parameters.get_admin("CHECK_REQUESTS_INTERVAL")) * 1000,
                'text': _("pending requests"),
            })
        )]

    if caller == 'domains':
        tpl = Template("""<script type="text/javascript">
$(document).bind('domform_init', function() {
    activate_widget.call($('#id_spam_subject_tag2_act'));
});
</script>
""")

        return [tpl.render(Context({}))]
    return []


@events.observe("TopNotifications")
def display_requests(user):
    from .sql_listing import get_wrapper

    if parameters.get_admin("USER_CAN_RELEASE") == "yes" \
            or user.group == "SimpleUsers":
        return []
    nbrequests = get_wrapper().get_pending_requests(user)

    url = reverse("modoboa.extensions.amavis.views.index")
    url += "#listing/?viewrequests=1"
    tpl = Template("""<ul class="nav pull-right {{ css }}">
  <li class="dropdown">
    <a href="#" class="dropdown-toggle" data-toggle="dropdown">
      <i class="icon-white icon-bell"></i> <span id="alerts-counter" class="label label-important">{{ nbrequests }}</span>
    </a>
    <ul class="dropdown-menu">
      <li>
        <a id="nbrequests" href="{{ url }}">
          <span class="label label-important">{{ nbrequests }}</span> {{ label }}
        </a>
      </li>
    </ul>
  </li>
</ul>""")
    css = "hidden" if nbrequests == 0 else ""
    return [tpl.render(Context(dict(
        label=_("Pending requests"), url=url, css=css,
        nbrequests=nbrequests
    )))]


def send_amavis_form():
    """
    """
    from .forms import DomainPolicyForm
    return [{
        'id': 'amavis', 'title': _("Content filter"), 'cls': DomainPolicyForm,
        'formtpl': 'amavis/domain_content_filter.html'
    }]


@events.observe("ExtraDomainForm")
def extra_domain_form(user, domain):
    if not user.has_perm("admin.view_domains"):
        return []
    return send_amavis_form()


@events.observe('ExtraRelayDomainForm')
def extra_relaydomain_form(user, rdomain):
    if not user.has_perm("postfix_relay_domains.add_relaydomain"):
        return []
    return send_amavis_form()


@events.observe("FillDomainInstances")
def fill_domain_instances(user, domain, instances):
    if not user.has_perm("admin.view_domains"):
        return
    instances["amavis"] = domain


@events.observe("FillRelayDomainInstances")
def fill_relaydomain_instances(user, rdomain, instances):
    if not user.has_perm("postfix_relay_domains.add_relaydomain"):
        return
    instances["amavis"] = rdomain
