"""Export related views."""

import cStringIO
import csv

from rfc6266 import build_header

from django.contrib.auth.decorators import (
    login_required, permission_required, user_passes_test
)
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext as _

from ..forms import ExportIdentitiesForm, ExportDomainsForm
from ..lib import get_domains, get_identities


def _export(content, filename):
    """Export a csv file's content

    :param content: the content to export (string)
    :param filename: the name that will appear into the response
    :return: an ``HttpResponse`` object
    """
    resp = HttpResponse(content)
    resp["Content-Type"] = "text/csv"
    resp["Content-Length"] = len(content)
    resp["Content-Disposition"] = build_header(filename)
    return resp


@login_required
@user_passes_test(
    lambda u: u.has_perm("core.add_user") or u.has_perm("admin.add_alias")
)
def export_identities(request):
    ctx = {
        "title": _("Export identities"),
        "action_label": _("Export"),
        "action_classes": "submit",
        "formid": "exportform",
        "action": reverse("admin:identity_export"),
    }

    if request.method == "POST":
        form = ExportIdentitiesForm(request.POST)
        form.is_valid()
        fp = cStringIO.StringIO()
        csvwriter = csv.writer(fp, delimiter=form.cleaned_data["sepchar"])
        identities = get_identities(
            request.user, **request.session['identities_filters'])
        for ident in identities:
            ident.to_csv(csvwriter)
        content = fp.getvalue()
        fp.close()
        return _export(content, form.cleaned_data["filename"])

    ctx["form"] = ExportIdentitiesForm()
    return render(request, "common/generic_modal_form.html", ctx)


@login_required
@permission_required("admin.add_domain")
def export_domains(request):
    ctx = {
        "title": _("Export domains"),
        "action_label": _("Export"),
        "action_classes": "submit",
        "formid": "exportform",
        "action": reverse("admin:domain_export"),
    }

    if request.method == "POST":
        form = ExportDomainsForm(request.POST)
        form.is_valid()
        fp = cStringIO.StringIO()
        csvwriter = csv.writer(fp, delimiter=form.cleaned_data["sepchar"])
        for dom in get_domains(request.user,
                               **request.session['domains_filters']):
            dom.to_csv(csvwriter)
        content = fp.getvalue()
        fp.close()
        return _export(content, form.cleaned_data["filename"])

    ctx["form"] = ExportDomainsForm()
    return render(request, "common/generic_modal_form.html", ctx)
