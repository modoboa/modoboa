# -*- coding: utf-8 -*-

"""Identity related views."""

from __future__ import unicode_literals

from reversion import revisions as reversion

from django.contrib.auth import mixins as auth_mixins
from django.contrib.auth.decorators import (
    login_required, permission_required, user_passes_test
)
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _, ungettext
from django.views import generic
from django.views.decorators.csrf import ensure_csrf_cookie

from modoboa.core.models import User
from modoboa.lib.exceptions import BadRequest, PermDeniedException
from modoboa.lib.listing import get_listing_page, get_sort_order
from modoboa.lib.web_utils import render_to_json_response
from .. import signals
from ..forms import AccountForm, AccountWizard
from ..lib import get_identities
from ..models import Domain, Mailbox


@login_required
@user_passes_test(
    lambda u: u.has_perm("core.add_user") or
    u.has_perm("admin.add_alias")
)
def _identities(request):
    filters = {
        fname: request.GET.get(fname, None)
        for fname in ["searchquery", "idtfilter", "grpfilter"]
    }
    request.session["identities_filters"] = filters
    idents_list = get_identities(request.user, **filters)
    sort_order, sort_dir = get_sort_order(request.GET, "identity",
                                          ["identity", "name_or_rcpt", "tags"])
    if sort_order in ["identity", "name_or_rcpt"]:
        objects = sorted(idents_list, key=lambda o: getattr(o, sort_order),
                         reverse=sort_dir == "-")
    else:
        objects = sorted(idents_list, key=lambda o: o.tags[0]["label"],
                         reverse=sort_dir == "-")
    context = {
        "handle_mailboxes": request.localconfig.parameters.get_value(
            "handle_mailboxes", raise_exception=False)
    }
    page = get_listing_page(objects, request.GET.get("page", 1))
    context["headers"] = render_to_string(
        "admin/identity_headers.html", {}, request)
    if page is None:
        context["length"] = 0
    else:
        context["rows"] = render_to_string(
            "admin/identities_table.html", {
                "identities": page.object_list
            }, request
        )
        context["pages"] = [page.number]
    return render_to_json_response(context)


@login_required
@permission_required("admin.add_mailbox")
def list_quotas(request):
    from modoboa.lib.db_utils import db_type

    sort_order, sort_dir = get_sort_order(request.GET, "address")
    mboxes = Mailbox.objects.get_for_admin(
        request.user, request.GET.get("searchquery", None)
    )
    mboxes = mboxes.exclude(quota=0)
    if sort_order in ["address", "quota"]:
        mboxes = mboxes.order_by("%s%s" % (sort_dir, sort_order))
    elif sort_order in ("quota_value__bytes", "quota_usage"):
        db_type = db_type()
        if db_type == "mysql":
            where = "CONCAT(admin_mailbox.address,'@',admin_domain.name)"
        else:
            where = "admin_mailbox.address||'@'||admin_domain.name"
        if sort_order == "quota_value__bytes":
            mboxes = mboxes.extra(
                select={"quota_value__bytes": "admin_quota.bytes"},
                where=["admin_quota.username=%s" % where],
                tables=["admin_quota", "admin_domain"],
                order_by=["%s%s" % (sort_dir, sort_order)]
            )
        else:
            if db_type == "postgres":
                select = (
                    "(admin_quota.bytes::float / (CAST(admin_mailbox.quota "
                    "AS BIGINT) * 1048576)) * 100"
                )
            else:
                select = (
                    "(admin_quota.bytes * 1.0 / (admin_mailbox.quota "
                    "* 1048576)) * 100"
                )
            mboxes = mboxes.extra(
                select={"quota_usage": select},
                where=["admin_quota.username=%s" % where],
                tables=["admin_quota", "admin_domain"],
                order_by=["%s%s" % (sort_dir, sort_order)]
            )
    else:
        raise BadRequest(_("Invalid request"))
    page = get_listing_page(mboxes, request.GET.get("page", 1))
    context = {
        "headers": render_to_string(
            "admin/identities_quota_headers.html", {}, request
        )
    }
    if page is None:
        context["length"] = 0
    else:
        context["rows"] = render_to_string(
            "admin/identities_quotas.html", {"mboxes": page}, request
        )
        context["pages"] = [page.number]
    return render_to_json_response(context)


@login_required
@user_passes_test(
    lambda u: u.has_perm("admin.add_user") or
    u.has_perm("admin.add_alias") or
    u.has_perm("admin.add_mailbox")
)
def get_next_page(request):
    """Return the next page of the identity list."""
    if request.GET.get("objtype", "identity") == "identity":
        return _identities(request)
    return list_quotas(request)


@login_required
@user_passes_test(
    lambda u: u.has_perm("admin.add_user") or
    u.has_perm("admin.add_alias")
)
@ensure_csrf_cookie
def identities(request, tplname="admin/identities.html"):
    return render(request, tplname, {
        "selection": "identities",
        "deflocation": "list/"
    })


@login_required
@permission_required("core.add_user")
def accounts_list(request):
    accs = User.objects.filter(is_superuser=False) \
        .exclude(groups__name="SimpleUsers")
    res = [a.username for a in accs.all()]
    return render_to_json_response(res)


@login_required
@permission_required("core.add_user")
@reversion.create_revision()
def newaccount(request):
    """Create a new account."""
    return AccountWizard(request).process()


@login_required
@permission_required("core.change_user")
@reversion.create_revision()
def editaccount(request, pk):
    account = User.objects.get(pk=pk)
    if not request.user.can_access(account):
        raise PermDeniedException
    mb = account.mailbox if hasattr(account, "mailbox") else None

    instances = {
        "general": account, "profile": account, "mail": mb, "perms": account
    }
    results = signals.get_account_form_instances.send(
        sender="editaccount", user=request.user, account=account)
    for result in results:
        instances.update(result[1])
    return AccountForm(request, instances=instances).process()


@login_required
@permission_required("core.delete_user")
def delaccount(request, pk):
    User.objects.get(pk=pk).delete()
    return render_to_json_response(
        ungettext("Account deleted", "Accounts deleted", 1)
    )


@login_required
@permission_required("admin.add_domain")
def remove_permission(request):
    domid = request.GET.get("domid", None)
    daid = request.GET.get("daid", None)
    if domid is None or daid is None:
        raise BadRequest(_("Invalid request"))
    try:
        account = User.objects.get(pk=daid)
        domain = Domain.objects.get(pk=domid)
    except (User.DoesNotExist, Domain.DoesNotExist):
        raise BadRequest(_("Invalid request"))
    if not request.user.can_access(account) or \
       not request.user.can_access(domain):
        raise PermDeniedException
    domain.remove_admin(account)
    return render_to_json_response({})


class AccountDetailView(
        auth_mixins.PermissionRequiredMixin, generic.DetailView):
    """DetailView for Account."""

    model = User
    permission_required = "core.add_user"
    template_name = "admin/account_detail.html"

    def has_permission(self):
        """Check object-level access."""
        result = super(AccountDetailView, self).has_permission()
        if not result:
            return result
        return self.request.user.can_access(self.get_object())

    def get_context_data(self, **kwargs):
        """Add information to context."""
        context = super(AccountDetailView, self).get_context_data(**kwargs)
        del context["user"]
        result = signals.extra_account_dashboard_widgets.send(
            self.__class__, user=self.request.user, account=self.object)
        context["templates"] = {"left": [], "right": []}
        for _receiver, widgets in result:
            for widget in widgets:
                context["templates"][widget["column"]].append(
                    widget["template"])
                context.update(widget["context"])
        if self.object.role in ["Resellers", "DomainAdmins"]:
            context["domains"] = Domain.objects.get_for_admin(self.object)
        context["selection"] = "identities"
        return context
