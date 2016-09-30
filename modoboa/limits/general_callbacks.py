"""General event callbacks."""

from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from modoboa.lib import events, parameters

from . import forms
from . import utils


@events.observe("ExtraAdminContent")
def display_pool_usage(user, target, currentpage):
    condition = (
        parameters.get_admin("ENABLE_ADMIN_LIMITS") == "no" or
        target != "leftcol" or user.is_superuser)
    if condition:
        return []
    if currentpage == "identities":
        names = ["mailboxes", "mailbox_aliases"]
        if user.has_perm("admin.add_domain"):
            names += ["domain_admins"]
    else:
        exceptions = ["domain_admins", "mailboxes", "mailbox_aliases"]
        names = [
            name for name, tpl in utils.get_user_limit_templates()
            if name not in exceptions and
            ("required_role" not in tpl or
             tpl["required_role"] == user.role)
        ]

    limits = user.userobjectlimit_set.filter(name__in=names, max_value__gt=0)
    if len(limits) == 0:
        return []
    return [
        render_to_string("limits/poolusage.html",
                         dict(limits=limits))
    ]


@events.observe("ExtraAccountForm")
def extra_account_form(user, account=None):
    if parameters.get_admin("ENABLE_ADMIN_LIMITS") == "no":
        return []
    if user.role not in ["SuperAdmins", "Resellers"]:
        return []
    condition = (
        (account is not None and
         account.role not in ["Resellers", "DomainAdmins"]) or
        user == account
    )
    if condition:
        return []

    return [{
        "id": "resources", "title": _("Resources"),
        "cls": forms.ResourcePoolForm
    }]


@events.observe("ExtraDomainForm")
def extra_domain_form(user, domain):
    """Include domain limits form."""
    if parameters.get_admin("ENABLE_DOMAIN_LIMITS") == "no":
        return []
    if not user.has_perm("admin.change_domain"):
        return []
    return [{
        "id": "resources", "title": _("Resources"),
        "cls": forms.DomainLimitsForm
    }]


@events.observe("FillDomainInstances")
def fill_domain_instances(user, domain, instances):
    """Set domain instance for resources form."""
    if parameters.get_admin("ENABLE_DOMAIN_LIMITS") == "no":
        return
    if not user.has_perm("admin.change_domain"):
        return
    instances["resources"] = domain


@events.observe("CheckExtraAccountForm")
def check_form_access(account, form):
    if form["id"] != "resources":
        return [True]
    if account.role not in ["Resellers", "DomainAdmins"]:
        return [False]
    return [True]


@events.observe("FillAccountInstances")
def fill_account_instances(user, account, instances):
    condition = (
        parameters.get_admin("ENABLE_ADMIN_LIMITS") == "no" or
        (not user.is_superuser and user.role != "Resellers")
    )
    if condition:
        return
    if account.role not in ["Resellers", "DomainAdmins"]:
        return
    instances["resources"] = account


@events.observe("GetStaticContent")
def get_static_content(caller, st_type, user):
    condition = (
        parameters.get_admin("ENABLE_ADMIN_LIMITS") == "no" or
        caller not in ["domains", "identities"] or
        user.role in ["SuperAdmins", "SimpleUsers"]
    )
    if condition:
        return []
    if st_type == "css":
        return ["""<style>
.resource {
    padding: 10px 15px;
}

.resource .progress {
    margin-bottom: 0px;
}

.resource .progress .bar {
    color: #000000;
}
</style>
"""]
    return ["""
<script type="text/javascript">
$(document).ready(function() {
    $(".progress").tooltip();
});
</script>
"""]
