"""General event callbacks."""

from django.utils.translation import ugettext as _

from modoboa.lib import events

from modoboa.admin.callbacks import PERMISSIONS as ADMIN_PERMS

from .forms import ResourcePoolForm
from .models import LimitTemplates


PERMISSIONS = {
    "Resellers": (
        ADMIN_PERMS.get("DomainAdmins") +
        [["admin", "domain", "view_domains"],
         ["admin", "domain", "add_domain"],
         ["admin", "domain", "change_domain"],
         ["admin", "domain", "delete_domain"]]
    )
}


@events.observe("GetExtraRoles")
def get_extra_roles(user, account):
    """Return additional roles."""
    if user.is_superuser:
        return [("Resellers", _("Reseller")), ]
    return []


@events.observe("GetExtraRolePermissions")
def extra_permissions(rolename):
    """Return extra permissions for Resellers."""
    return PERMISSIONS.get(rolename, [])


@events.observe("ExtraAdminContent")
def display_pool_usage(user, target, currentpage):
    from django.template.loader import render_to_string

    if target != "leftcol" or user.is_superuser:
        return []
    if currentpage == "identities":
        names = ["mailboxes_limit", "mailbox_aliases_limit"]
        if user.has_perm("admin.add_domain"):
            names += ["domain_admins_limit"]
    else:
        names = [
            tpl[0] for tpl in LimitTemplates().templates
            if tpl[0] not in ["domain_admins_limit", "mailboxes_limit",
                              "mailbox_aliases_limit"]
            and (len(tpl) == 3 or tpl[3] == user.group)
        ]

    limits = user.limitspool.limit_set.filter(name__in=names, maxvalue__gt=0)
    if len(limits) == 0:
        return []
    return [
        render_to_string("limits/poolusage.html",
                         dict(limits=limits))
    ]


@events.observe("ExtraAccountForm")
def extra_account_form(user, account=None):
    if user.group not in ["SuperAdmins", "Resellers"]:
        return []
    if account is not None and \
            account.group not in ["Resellers", "DomainAdmins"]:
        return []

    return [
        dict(
            id="resources", title=_("Resources"), cls=ResourcePoolForm
        )
    ]


@events.observe("CheckExtraAccountForm")
def check_form_access(account, form):
    if form["id"] != "resources":
        return [True]
    if not account.belongs_to_group("Resellers") and \
       not account.belongs_to_group("DomainAdmins"):
        return [False]
    return [True]


@events.observe("FillAccountInstances")
def fill_account_instances(user, account, instances):
    if not user.is_superuser and not user.belongs_to_group("Resellers"):
        return
    if not account.belongs_to_group("Resellers") and \
       not account.belongs_to_group("DomainAdmins"):
        return
    instances["resources"] = account


@events.observe("GetStaticContent")
def get_static_content(caller, st_type, user):
    if caller not in ['domains', 'identities']:
        return []
    if user.group == "SimpleUsers":
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
