# coding: utf-8

"""
The *limits* extension
----------------------
"""
from django.contrib.auth.models import Permission, Group
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.lib import events, parameters
from modoboa.core.extensions import ModoExtension, exts_pool
from .forms import ResourcePoolForm
import controls


class Limits(ModoExtension):
    name = "limits"
    label = "Limits"
    version = "1.0"
    description = ugettext_lazy(
        "Per administrator resources to limit the number of objects they can create"
    )

    def init(self):
        from modoboa.core.models import User
        from modoboa.extensions.admin.models import Domain

        ct = ContentType.objects.get(app_label="admin", model="domain")
        dagrp = Group.objects.get(name="DomainAdmins")

        grp = Group(name="Resellers")
        grp.save()
        grp.permissions.add(*dagrp.permissions.all())

        ct = ContentType.objects.get_for_model(Domain)
        for pname in ["view_domains", "add_domain", "change_domain", "delete_domain"]:
            perm = Permission.objects.get(content_type=ct, codename=pname)
            grp.permissions.add(perm)
            grp.save()

        for user in User.objects.filter(groups__name='DomainAdmins'):
            try:
                controls.create_pool(user)
            except IntegrityError:
                pass

    def load(self):
        from modoboa.extensions.limits.app_settings import ParametersForm
        parameters.register(ParametersForm, ugettext_lazy("Limits"))

    def destroy(self):
        parameters.unregister()
        Group.objects.get(name="Resellers").delete()

exts_pool.register_extension(Limits)


@events.observe("GetExtraRoles")
def get_extra_roles(user):
    if user.is_superuser:
        return [("Resellers", _("Reseller")), ]
    return []


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
        names = ["domains_limit", "domain_aliases_limit"]
    limits = user.limitspool.limit_set.filter(name__in=names, maxvalue__gt=0)
    if len(limits) == 0:
        return []
    return [render_to_string("limits/poolusage.html", dict(limits=limits))]


@events.observe("ExtraAccountForm")
def extra_account_form(user, account=None):
    if not user.group in ["SuperAdmins", "Resellers"]:
        return []
    if account is not None and not account.group in ["Resellers", "DomainAdmins"]:
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
def get_static_content(user):
    if user.group == "SimpleUsers":
        return []
    return """<style>
.resource {
    margin: 5px 0;
}

.resource .progress { 
    margin-bottom: 0px;
}

.resource .progress .bar {
    color: #000000;
}
</style>
<script type="text/javascript">
$(document).ready(function() {
    $(".progress").tooltip();
});
</script>
"""
