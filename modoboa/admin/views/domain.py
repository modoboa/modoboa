"""Domain related views."""

from functools import reduce

from reversion import revisions as reversion

from django.contrib.auth import mixins as auth_mixins
from django.contrib.auth.decorators import (
    login_required, permission_required, user_passes_test
)
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import ugettext as _, ungettext
from django.views import generic
from django.views.decorators.csrf import ensure_csrf_cookie

from modoboa.core import signals as core_signals
from modoboa.lib.exceptions import PermDeniedException
from modoboa.lib.listing import get_listing_page, get_sort_order
from modoboa.lib.web_utils import render_to_json_response
from modoboa.maillog import models as ml_models

from .. import signals
from ..forms import DomainForm, DomainWizard
from ..lib import get_domains
from ..models import Domain, Mailbox


@login_required
def index(request):
    return HttpResponseRedirect(reverse("admin:domain_list"))


@login_required
@user_passes_test(
    lambda u: u.has_perm("admin.view_domain") or
    u.has_perm("admin.view_mailbox")
)
def _domains(request):
    sort_order, sort_dir = get_sort_order(request.GET, "name")
    extra_filters = signals.extra_domain_filters.send(sender="_domains")
    if extra_filters:
        extra_filters = reduce(
            lambda a, b: a + b, [result[1] for result in extra_filters])
    filters = {
        flt: request.GET.get(flt, None)
        for flt in ["domfilter", "searchquery"] + extra_filters
    }
    request.session["domains_filters"] = filters
    domainlist = get_domains(request.user, **filters)
    if sort_order == "name":
        domainlist = sorted(
            domainlist,
            key=lambda d: getattr(d, sort_order), reverse=sort_dir == "-"
        )
    else:
        domainlist = sorted(domainlist, key=lambda d: d.tags[0]["name"],
                            reverse=sort_dir == "-")
    context = {
        "handle_mailboxes": request.localconfig.parameters.get_value(
            "handle_mailboxes", raise_exception=False),
        "auto_account_removal": request.localconfig.parameters.get_value(
            "auto_account_removal"),
    }
    page = get_listing_page(domainlist, request.GET.get("page", 1))
    parameters = request.localconfig.parameters
    dns_checks = {
        "enable_mx_checks": parameters.get_value("enable_mx_checks"),
        "enable_spf_checks": parameters.get_value("enable_spf_checks"),
        "enable_dkim_checks": parameters.get_value("enable_dkim_checks"),
        "enable_dmarc_checks": parameters.get_value("enable_dmarc_checks"),
        "enable_autoconfig_checks": (
            parameters.get_value("enable_autoconfig_checks")),
        "enable_dnsbl_checks": parameters.get_value("enable_dnsbl_checks")
    }
    context["headers"] = render_to_string(
        "admin/domain_headers.html", dns_checks, request
    )
    if page is None:
        context["length"] = 0
    else:
        tpl_context = {"domains": page.object_list}
        tpl_context.update(dns_checks)
        context["rows"] = render_to_string(
            "admin/domains_table.html", tpl_context, request
        )
        context["pages"] = [page.number]
    return render_to_json_response(context)


@login_required
@ensure_csrf_cookie
def domains(request, tplname="admin/domains.html"):
    if not request.user.has_perm("admin.view_domain"):
        if request.user.has_perm("admin.view_mailbox"):
            return HttpResponseRedirect(
                reverse("admin:identity_list")
            )
        return HttpResponseRedirect(reverse("core:user_index"))
    parameters = request.localconfig.parameters
    return render(request, tplname, {
        "selection": "domains",
        "enable_mx_checks": parameters.get_value("enable_mx_checks"),
        "enable_spf_checks": parameters.get_value("enable_spf_checks"),
        "enable_dkim_checks": parameters.get_value("enable_dkim_checks"),
        "enable_dmarc_checks": parameters.get_value("enable_dmarc_checks"),
        "enable_autoconfig_checks": (
            parameters.get_value("enable_autoconfig_checks")),
        "enable_dnsbl_checks": parameters.get_value("enable_dnsbl_checks")
    })


@login_required
@user_passes_test(
    lambda u: u.has_perm("admin.view_domain") or
    u.has_perm("admin.view_mailbox") or
    u.has_perm("admin.add_domain")
)
def get_next_page(request):
    """Return the next page of the domain or quota list."""
    objtype = request.GET.get("objtype", "domain")
    if objtype == "domain":
        return _domains(request)
    if objtype == "quota":
        return list_quotas(request)
    return list_logs(request)


@login_required
@permission_required("core.add_user")
def domains_list(request):
    doms = [dom.name for dom in Domain.objects.get_for_admin(request.user)]
    return render_to_json_response(doms)


@login_required
@permission_required("admin.view_domain")
def list_quotas(request):
    sort_order, sort_dir = get_sort_order(request.GET, "name")
    domains = Domain.objects.get_for_admin(request.user)
    domains = domains.exclude(quota=0)
    if sort_order in ["name", "quota"]:
        domains = domains.order_by("{}{}".format(sort_dir, sort_order))
    elif sort_order == "allocated_quota":
        domains = (
            domains.annotate(allocated_quota=Sum("mailbox__quota"))
            .order_by("{}{}".format(sort_dir, sort_order))
        )
    page = get_listing_page(domains, request.GET.get("page", 1))
    context = {
        "headers": render_to_string(
            "admin/domains_quota_headers.html", {}, request
        )
    }
    if page is None:
        context["length"] = 0
    else:
        context["rows"] = render_to_string(
            "admin/domains_quotas.html", {"domains": page}, request
        )
        context["pages"] = [page.number]
    return render_to_json_response(context)


@login_required
@permission_required("admin.view_domain")
def list_logs(request):
    """List all Maillog entries."""
    sort_order, sort_dir = get_sort_order(request.GET, "date")
    search = request.GET.get("searchquery")
    if not request.user.is_superuser:
        domains = Domain.objects.get_for_admin(request.user)
        logs = ml_models.Maillog.objects.filter(
            Q(from_domain__in=domains) | Q(to_domain__in=domains)
        )
    else:
        logs = ml_models.Maillog.objects.all()
    logs = logs.order_by("{}{}".format(sort_dir, sort_order))
    if search:
        logs = logs.filter(
            Q(sender__icontains=search) |
            Q(rcpt__icontains=search) |
            Q(queue_id__icontains=search) |
            Q(status__icontains=search)
        )
    page = get_listing_page(logs, request.GET.get("page", 1))
    context = {
        "headers": render_to_string(
            "admin/domains_log_headers.html", {}, request
        )
    }
    if page is None:
        context["length"] = 0
    else:
        context["rows"] = render_to_string(
            "admin/domains_logs.html", {"logs": page}, request
        )
        context["pages"] = [page.number]
    return render_to_json_response(context)


@login_required
@permission_required("admin.add_domain")
@reversion.create_revision()
def newdomain(request):
    core_signals.can_create_object.send(
        "newdomain", context=request.user, klass=Domain)
    return DomainWizard(request).process()


@login_required
@permission_required("admin.view_domain")
@reversion.create_revision()
def editdomain(request, dom_id):
    """Edit domain view."""
    domain = Domain.objects.get(pk=dom_id)
    if not request.user.can_access(domain):
        raise PermDeniedException

    instances = {"general": domain}
    results = signals.get_domain_form_instances.send(
        sender="editdomain", user=request.user, domain=domain)
    for result in results:
        instances.update(result[1])
    return DomainForm(request, instances=instances).process()


@login_required
@permission_required("admin.delete_domain")
def deldomain(request, dom_id):
    keepdir = request.POST.get("keepdir", "false") == "true"
    try:
        mb = Mailbox.objects.get(user__id=request.user.id)
    except Mailbox.DoesNotExist:
        mb = None

    dom = Domain.objects.get(pk=dom_id)
    if not request.user.can_access(dom):
        raise PermDeniedException
    if mb and mb.domain == dom:
        raise PermDeniedException(_("You can't delete your own domain"))
    dom.delete(request.user, keepdir)

    msg = ungettext("Domain deleted", "Domains deleted", 1)
    return render_to_json_response(msg)


class DomainDetailView(
        auth_mixins.PermissionRequiredMixin, generic.DetailView):
    """DetailView for Domain."""

    model = Domain
    permission_required = "admin.view_domain"

    def get_queryset(self):
        """Add some prefetching."""
        return (
            Domain.objects.get_for_admin(self.request.user)
            .prefetch_related("domainalias_set", "mailbox_set", "alias_set")
        )

    def get_context_data(self, **kwargs):
        """Include extra widgets."""
        context = super(DomainDetailView, self).get_context_data(**kwargs)
        result = signals.extra_domain_dashboard_widgets.send(
            self.__class__, user=self.request.user, domain=self.object)
        parameters = self.request.localconfig.parameters
        context.update({
            "templates": {"left": [], "right": []},
            "enable_mx_checks": parameters.get_value("enable_mx_checks"),
            "enable_spf_checks": parameters.get_value("enable_spf_checks"),
            "enable_dkim_checks": parameters.get_value("enable_dkim_checks"),
            "enable_dmarc_checks": parameters.get_value("enable_dmarc_checks"),
            "enable_autoconfig_checks": (
                parameters.get_value("enable_autoconfig_checks")),
            "enable_dnsbl_checks": parameters.get_value("enable_dnsbl_checks"),
        })
        for _receiver, widgets in result:
            for widget in widgets:
                context["templates"][widget["column"]].append(
                    widget["template"])
                # FIXME: can raise conflicts...
                context.update(widget["context"])

        return context


class DomainAlarmsView(
        auth_mixins.PermissionRequiredMixin, generic.DetailView):
    """A view to list domain alarms."""

    model = Domain
    permission_required = "admin.view_domain"
    template_name = "admin/domain_alarms.html"

    def get_queryset(self):
        """Add some prefetching."""
        return (
            Domain.objects.get_for_admin(self.request.user)
            .prefetch_related("alarms")
        )
