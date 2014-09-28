import reversion
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _, ungettext
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import (
    login_required, permission_required, user_passes_test
)
from modoboa.lib import parameters, events
from modoboa.lib.webutils import (
    _render_to_string, render_to_json_response
)
from modoboa.lib.exceptions import (
    PermDeniedException
)
from modoboa.lib.templatetags.lib_tags import pagination_bar
from modoboa.lib.listing import get_sort_order, get_listing_page
from modoboa.extensions.admin.models import Domain, Mailbox
from modoboa.extensions.admin.forms import (
    DomainForm
)
from modoboa.extensions.admin.lib import get_domains


@login_required
def index(request):
    return HttpResponseRedirect(reverse("admin:domain_list"))


@login_required
@user_passes_test(
    lambda u: u.has_perm("admin.view_domains") or u.has_perm("admin.view_mailboxes")
)
def _domains(request):
    sort_order, sort_dir = get_sort_order(request.GET, "name")
    filters = dict(
        (flt, request.GET.get(flt, None))
        for flt in ['domfilter', 'searchquery']
        + events.raiseQueryEvent('ExtraDomainFilters')
    )
    request.session['domains_filters'] = filters
    domainlist = get_domains(
        request.user, **filters
    )
    if sort_order == 'name':
        domainlist = sorted(
            domainlist,
            key=lambda d: getattr(d, sort_order), reverse=sort_dir == '-'
        )
    else:
        domainlist = sorted(domainlist, key=lambda d: d.tags[0],
                            reverse=sort_dir == '-')
    page = get_listing_page(domainlist, request.GET.get("page", 1))
    return render_to_json_response({
        "table": _render_to_string(request, 'admin/domains_table.html', {
            'domains': page.object_list,
            'tableid': 'domains'
        }),
        "page": page.number,
        "paginbar": pagination_bar(page),
        "handle_mailboxes": parameters.get_admin("HANDLE_MAILBOXES",
                                                 raise_error=False),
        "auto_account_removal": parameters.get_admin("AUTO_ACCOUNT_REMOVAL")
    })


@login_required
@ensure_csrf_cookie
def domains(request, tplname="admin/domains.html"):
    if not request.user.has_perm("admin.view_domains"):
        if request.user.has_perm("admin.view_mailboxes"):
            return HttpResponseRedirect(
                reverse("admin:identity_list")
            )
        return HttpResponseRedirect(reverse("core:user_index"))
    return render(request, tplname, {"selection": "domains"})


@login_required
@permission_required("core.add_user")
def domains_list(request):
    doms = [dom.name for dom in Domain.objects.get_for_admin(request.user)]
    return render_to_json_response(doms)


@login_required
@permission_required("admin.add_domain")
@transaction.commit_on_success
@reversion.create_revision()
def newdomain(request):
    from modoboa.extensions.admin.forms import DomainWizard

    events.raiseEvent("CanCreate", request.user, "domains")
    return DomainWizard(request).process()


@login_required
@permission_required("admin.view_domains")
@transaction.commit_on_success
@reversion.create_revision()
def editdomain(request, dom_id):
    """Edit domain view."""
    domain = Domain.objects.get(pk=dom_id)
    if not request.user.can_access(domain):
        raise PermDeniedException

    instances = dict(general=domain)
    events.raiseEvent("FillDomainInstances", request.user, domain, instances)
    return DomainForm(request, instances=instances).process()


@login_required
@permission_required("admin.delete_domain")
@transaction.commit_on_success
def deldomain(request, dom_id):
    keepdir = True if request.POST.get("keepdir", "false") == "true" else False
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
