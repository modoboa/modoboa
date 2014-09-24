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
             "url": reverse('amavis:index')}
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
def check_for_pending_requests(user, include_all):
    """
    Check if release requests are pending.
    """
    from .sql_connector import get_connector

    if parameters.get_admin("USER_CAN_RELEASE") == "yes" \
            or user.group == "SimpleUsers":
        return []

    nbrequests = get_connector(user=user).get_pending_requests()
    if not nbrequests:
        return [{"id": "nbrequests", "counter": 0}] if include_all \
            else []

    url = reverse("amavis:index")
    url += "#listing/?viewrequests=1"
    return [{
        "id": "nbrequests", "url": url, "text": _("Pending requests"),
        "counter": nbrequests, "level": "important"
    }]


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
