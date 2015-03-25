from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.template import Template, Context

from modoboa.lib import events, parameters
from modoboa.extensions.admin.models import DomainAlias, Alias
from modoboa.extensions.amavis.lib import (
    create_user_and_policy, update_user_and_policy, delete_user_and_policy,
    create_user_and_use_policy, delete_user
)
from .lib import manual_learning_enabled
from .models import Policy, Users


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
    create_user_and_policy("@{0}".format(domain.name))


@events.observe("DomainModified")
def on_domain_modified(domain):
    update_user_and_policy(
        "@{0}".format(domain.oldname),
        "@{0}".format(domain.name)
    )


@events.observe("DomainDeleted")
def on_domain_deleted(domain):
    delete_user_and_policy("@{0}".format(domain.name))


@events.observe("DomainAliasCreated")
def on_domain_alias_created(user, domainalias):
    create_user_and_use_policy(
        "@{0}".format(domainalias.name),
        "@{0}".format(domainalias.target.name)
    )


@events.observe("DomainAliasDeleted")
def on_domain_alias_deleted(domainaliases):
    if isinstance(domainaliases, DomainAlias):
        domainaliases = [domainaliases]
    for domainalias in domainaliases:
        delete_user("@{0}".format(domainalias.name))


@events.observe("MailboxModified")
def on_mailbox_modified(mailbox):
    """Update amavis records if address has changed."""
    if parameters.get_admin("MANUAL_LEARNING") == "no" or \
       not hasattr(mailbox, "old_full_address") or \
       mailbox.full_address == mailbox.old_full_address:
        return
    user = Users.objects.select_related().get(email=mailbox.old_full_address)
    full_address = mailbox.full_address
    user.email = full_address
    user.policy.policy_name = full_address[:32]
    user.policy.sa_username = full_address
    user.policy.save()
    user.save()


@events.observe("MailboxDeleted")
def on_mailbox_deleted(mailbox):
    """Clean amavis database when a mailbox is removed."""
    if parameters.get_admin("MANUAL_LEARNING") == "no":
        return
    delete_user_and_policy("@{0}".format(mailbox.full_address))


@events.observe("MailboxAliasCreated")
def on_mailboxalias_created(user, alias):
    """Create amavis record for the new alias.

    FIXME: how to deal with distibution lists ?
    """
    if not manual_learning_enabled(user) or alias.type != "alias":
        return
    try:
        policy = Policy.objects.get(
            policy_name=alias.mboxes.all()[0].full_address
        )
    except Policy.DoesNotExist:
        return
    else:
        email = alias.full_address
        Users.objects.create(
            email=email, policy=policy, fullname=email, priority=7
        )


@events.observe("MailboxAliasDeleted")
def on_mailboxalias_deleted(aliases):
    """Clean amavis database when an alias is removed."""
    if parameters.get_admin("MANUAL_LEARNING") == "no":
        return
    if isinstance(aliases, Alias):
        aliases = [aliases]
    aliases = [alias.full_address for alias in aliases]
    Users.objects.filter(email__in=aliases).delete()


@events.observe("GetStaticContent")
def extra_static_content(caller, st_type, user):
    if user.group == "SimpleUsers" or st_type != "js":
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
def check_for_pending_requests(request, include_all):
    """
    Check if release requests are pending.
    """
    from .sql_connector import get_connector

    if parameters.get_admin("USER_CAN_RELEASE") == "yes" \
            or request.user.group == "SimpleUsers":
        return []

    nbrequests = get_connector(user=request.user).get_pending_requests()
    if not nbrequests:
        return [{"id": "nbrequests", "counter": 0}] if include_all \
            else []

    url = reverse("amavis:index")
    url += "#listing/?viewrequests=1"
    return [{
        "id": "nbrequests", "url": url, "text": _("Pending requests"),
        "counter": nbrequests, "level": "danger"
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
