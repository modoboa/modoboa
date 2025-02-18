"""Import related views."""

from reversion import revisions as reversion

from django.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _

from .. import lib
from ..forms import ImportDataForm, ImportIdentitiesForm


@reversion.create_revision()
def importdata(request, formclass=ImportDataForm):
    """Generic import function

    As the process of importing data from a CSV file is the same
    whatever the type, we do a maximum of the work here.

    :param request: a ``Request`` instance
    :param typ: a string indicating the object type being imported
    :return: a ``Response`` instance
    """
    msg = None
    form = formclass(request.POST, request.FILES)
    if form.is_valid():
        status, msg = lib.import_data(
            request.user, request.FILES["sourcefile"], form.cleaned_data
        )
        if status:
            return render(
                request, "admin/import_done.html", {"status": "ok", "msg": msg}
            )
    return render(request, "admin/import_done.html", {"status": "ko", "msg": msg})


@login_required
@permission_required("admin.add_domain")
def import_domains(request):
    if request.method == "POST":
        return importdata(request)

    ctx = {
        "title": _("Import domains"),
        "action_label": _("Import"),
        "action_classes": "submit",
        "action": reverse("admin:domain_import"),
        "formid": "importform",
        "enctype": "multipart/form-data",
        "target": "import_target",
        "form": ImportDataForm(),
    }
    return render(request, "admin/import_domains_form.html", ctx)


@login_required
@user_passes_test(
    lambda u: u.has_perm("core.add_user") or u.has_perm("admin.add_alias")
)
def import_identities(request):
    if request.method == "POST":
        return importdata(request, ImportIdentitiesForm)

    ctx = {
        "title": _("Import identities"),
        "action_label": _("Import"),
        "action_classes": "submit",
        "action": reverse("admin:identity_import"),
        "formid": "importform",
        "enctype": "multipart/form-data",
        "target": "import_target",
        "form": ImportIdentitiesForm(),
    }
    return render(request, "admin/import_identities_form.html", ctx)
