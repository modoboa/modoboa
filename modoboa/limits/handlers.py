"""Django signal handlers for limits."""

from django.contrib.contenttypes.models import ContentType
from django.db.models import signals
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from modoboa.admin import models as admin_models, signals as admin_signals
from modoboa.core import models as core_models, signals as core_signals
from modoboa.lib import permissions, signals as lib_signals
from modoboa.parameters import tools as param_tools
from . import forms, lib, models, utils


@receiver(core_signals.can_create_object)
def check_object_limit(sender, context, **kwargs):
    """Check if user can create a new object."""
    if context.__class__.__name__ == "User":
        if not param_tools.get_global_parameter("enable_admin_limits"):
            return
        if context.is_superuser:
            return True
        ct = ContentType.objects.get_for_model(kwargs.get("klass"))
        limits = context.userobjectlimit_set.filter(content_type=ct)
    elif context.__class__.__name__ == "Domain":
        if not param_tools.get_global_parameter("enable_domain_limits"):
            return
        object_type = kwargs.get("object_type")
        limits = context.domainobjectlimit_set.filter(name=object_type)
    else:
        raise NotImplementedError
    for limit in limits:
        if limit.is_exceeded(kwargs.get("count", 1), kwargs.get("instance")):
            raise lib.LimitReached(limit)


@receiver(signals.post_save, sender=core_models.User)
def create_user_limits(sender, instance, **kwargs):
    """Create limits for new user."""
    if not kwargs.get("created"):
        return
    request = lib_signals.get_request()
    creator = request.user if request else None
    global_params = dict(param_tools.get_global_parameters("limits"))
    for name, definition in utils.get_user_limit_templates():
        ct = ContentType.objects.get_by_natural_key(
            *definition["content_type"].split("."))
        max_value = 0
        # creator can be None if user was created by a factory
        if not creator or creator.is_superuser:
            max_value = global_params["deflt_user_{0}_limit".format(name)]
        models.UserObjectLimit.objects.create(
            user=instance, name=name, content_type=ct, max_value=max_value)


@receiver(signals.post_save, sender=admin_models.Domain)
def create_domain_limits(sender, instance, **kwargs):
    """Create limits for new domain."""
    if not kwargs.get("created"):
        return
    global_params = dict(param_tools.get_global_parameters("limits"))
    for name, _definition in utils.get_domain_limit_templates():
        max_value = global_params["deflt_domain_{0}_limit".format(name)]
        models.DomainObjectLimit.objects.create(
            domain=instance, name=name, max_value=max_value)


@receiver(admin_signals.extra_domain_dashboard_widgets)
def display_domain_limits(sender, user, domain, **kwargs):
    """Display resources usage for domain."""
    if not param_tools.get_global_parameter("enable_domain_limits"):
        return []
    return [{
        "column": "right",
        "template": "limits/resources_widget.html",
        "context": {
            "limits": domain.domainobjectlimit_set.all()
        }
    }]


@receiver(admin_signals.extra_account_dashboard_widgets)
def display_admin_limits(sender, user, account, **kwargs):
    """Display resources usage for admin."""
    condition = (
        param_tools.get_global_parameter("enable_admin_limits") and
        account.role in ["DomainAdmins", "Resellers"]
    )
    if not condition:
        return []
    return [{
        "column": "right",
        "template": "limits/resources_widget.html",
        "context": {
            "limits": (
                account.userobjectlimit_set.select_related("content_type"))
        }
    }]


@receiver(admin_signals.extra_account_forms)
def extra_account_form(sender, user, account=None, **kwargs):
    """Add limits form."""
    if not param_tools.get_global_parameter("enable_admin_limits"):
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


@receiver(admin_signals.check_extra_account_form)
def check_form_access(sender, account, form, **kwargs):
    """Check if form must be used for account."""
    if form["id"] != "resources":
        return True
    if account.role not in ["Resellers", "DomainAdmins"]:
        return False
    return True


@receiver(admin_signals.get_account_form_instances)
def fill_account_instances(sender, user, account, **kwargs):
    """Set account instance for resources form."""
    condition = (
        not param_tools.get_global_parameter("enable_admin_limits") or
        (not user.is_superuser and user.role != "Resellers") or
        account.role not in ["Resellers", "DomainAdmins"]
    )
    if condition:
        return {}
    return {"resources": account}


@receiver(admin_signals.extra_domain_forms)
def extra_domain_form(sender, user, domain, **kwargs):
    """Include domain limits form."""
    if not param_tools.get_global_parameter("enable_domain_limits"):
        return []
    if not user.has_perm("admin.change_domain"):
        return []
    return [{
        "id": "resources", "title": _("Resources"),
        "cls": forms.DomainLimitsForm
    }]


@receiver(admin_signals.get_domain_form_instances)
def fill_domain_instances(sender, user, domain, **kwargs):
    """Set domain instance for resources form."""
    condition = (
        not param_tools.get_global_parameter("enable_domain_limits") or
        not user.has_perm("admin.change_domain")
    )
    if condition:
        return {}
    return {"resources": domain}


@receiver(core_signals.account_deleted)
def move_resource(sender, user, **kwargs):
    """Move remaining resource to another user."""
    owner = permissions.get_object_owner(user)
    if owner.is_superuser or owner.role != "Resellers":
        return
    utils.move_pool_resource(owner, user)


@receiver(core_signals.user_can_set_role)
def user_can_set_role(sender, user, role, account=None, **kwargs):
    """Check if the user can still set this role.

    The only interesting case concerns resellers defining new domain
    administrators. We want to check if they are allowed to do this
    operation before any modification is made to :keyword:`account`.

    :param ``User`` user: connected user
    :param str role: role to check
    :param ``User`` account: account modified (None on creation)
    """
    condition = (
        not param_tools.get_global_parameter("enable_admin_limits") or
        role != "DomainAdmins")
    if condition:
        return True
    lname = "domain_admins"
    condition = (
        user.is_superuser or
        not user.userobjectlimit_set.get(name=lname).is_exceeded()
    )
    if condition:
        return True
    if account is not None and account.role == role:
        return True
    return False


@receiver(core_signals.extra_static_content)
def get_static_content(sender, caller, st_type, user, **kwargs):
    """Add extra static content."""
    condition = (
        not param_tools.get_global_parameter("enable_admin_limits") or
        caller not in ["domains", "identities"] or
        user.role in ["SuperAdmins", "SimpleUsers"]
    )
    if condition:
        return ""
    if st_type == "css":
        return """<style>
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
"""
    return """
<script type="text/javascript">
$(document).ready(function() {
    $(".progress").tooltip();
});
</script>
"""


@receiver(admin_signals.extra_admin_content)
def display_pool_usage(sender, user, location, currentpage, **kwargs):
    """Display current usage."""
    condition = (
        not param_tools.get_global_parameter("enable_admin_limits") or
        location != "leftcol" or user.is_superuser)
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
                         {"limits": limits})
    ]


@receiver(core_signals.account_role_changed)
def move_pool_resource(sender, account, role, **kwargs):
    """Move remaining resource to owner if needed."""
    owner = permissions.get_object_owner(account)
    if not owner or owner.is_superuser or owner.role != "Resellers":
        # Domain admins can't change the role so nothing to check.
        return

    if role not in ["DomainAdmins", "Resellers"]:
        utils.move_pool_resource(owner, account)
