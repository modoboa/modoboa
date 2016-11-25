"""Import related views."""

import csv

from django.contrib.auth.decorators import (
    login_required, permission_required, user_passes_test
)
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import render
from django.utils.translation import ugettext as _

from reversion import revisions as reversion

from modoboa.lib.exceptions import ModoboaException, Conflict

from ..forms import ImportIdentitiesForm, ImportDataForm
from .. import lib
from .. import signals


@reversion.create_revision()
def importdata(request, formclass=ImportDataForm):
    """Generic import function

    As the process of importing data from a CSV file is the same
    whatever the type, we do a maximum of the work here.

    :param request: a ``Request`` instance
    :param typ: a string indicating the object type being imported
    :return: a ``Response`` instance
    """
    error = None
    form = formclass(request.POST, request.FILES)
    if form.is_valid():
        try:
            reader = csv.reader(request.FILES['sourcefile'],
                                delimiter=form.cleaned_data['sepchar'])
        except csv.Error as inst:
            error = str(inst)

        if error is None:
            try:
                cpt = 0
                for row in reader:
                    if not row:
                        continue
                    try:
                        fct = getattr(lib, "import_%s" % row[0].strip())
                    except AttributeError:
                        fct = signals.import_object.send(
                            sender="importdata", objtype=row[0].strip())
                        if not fct:
                            continue
                        fct = fct[0][1]
                    with transaction.atomic():
                        try:
                            fct(request.user, row, form.cleaned_data)
                        except Conflict:
                            if form.cleaned_data["continue_if_exists"]:
                                continue
                            raise Conflict(
                                _("Object already exists: %s"
                                  % form.cleaned_data['sepchar'].join(row[:2]))
                            )
                    cpt += 1
                msg = _("%d objects imported successfully" % cpt)
                return render(request, "admin/import_done.html", {
                    "status": "ok", "msg": msg
                })
            except (ModoboaException) as e:
                error = str(e)

    return render(request, "admin/import_done.html", {
        "status": "ko", "msg": error
    })


@login_required
@permission_required("admin.add_domain")
def import_domains(request):
    if request.method == "POST":
        return importdata(request)

    ctx = dict(
        title=_("Import domains"),
        action_label=_("Import"),
        action_classes="submit",
        action=reverse("admin:domain_import"),
        formid="importform",
        enctype="multipart/form-data",
        target="import_target",
        form=ImportDataForm()
    )
    return render(request, "admin/import_domains_form.html", ctx)


@login_required
@user_passes_test(
    lambda u: u.has_perm("core.add_user") or
    u.has_perm("admin.add_alias")
)
def import_identities(request):
    if request.method == "POST":
        return importdata(request, ImportIdentitiesForm)

    ctx = dict(
        title=_("Import identities"),
        action_label=_("Import"),
        action_classes="submit",
        action=reverse("admin:identity_import"),
        formid="importform",
        enctype="multipart/form-data",
        target="import_target",
        form=ImportIdentitiesForm()
    )
    return render(request, "admin/import_identities_form.html", ctx)
