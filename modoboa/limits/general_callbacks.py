"""General event callbacks."""

from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from modoboa.lib import events
from modoboa.parameters import tools as param_tools

from . import forms
from . import utils


@events.observe("ExtraAccountForm")
def extra_account_form(user, account=None):
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


@events.observe("ExtraDomainForm")
def extra_domain_form(user, domain):
    """Include domain limits form."""
    if not param_tools.get_global_parameter("enable_domain_limits"):
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
    if not param_tools.get_global_parameter("enable_domain_limits"):
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
        not param_tools.get_global_parameter("enable_admin_limits") or
        (not user.is_superuser and user.role != "Resellers")
    )
    if condition:
        return
    if account.role not in ["Resellers", "DomainAdmins"]:
        return
    instances["resources"] = account
