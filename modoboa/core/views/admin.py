from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import (
    login_required, user_passes_test
)
from modoboa.lib import parameters
from modoboa.lib.webutils import (
    _render_to_string, render_to_json_response
)
from modoboa.lib.listing import get_sort_order, get_listing_page
from modoboa.core.models import Extension, Log
from modoboa.core.tables import ExtensionsTable


@login_required
@user_passes_test(lambda u: u.is_superuser)
def viewsettings(request, tplname='core/settings_header.html'):
    return render(request, tplname, {
        "selection": "settings"
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def viewparameters(request, tplname='core/parameters.html'):
    return render_to_json_response({
        "status": "ok",
        "left_selection": "parameters",
        "content": _render_to_string(request, tplname, {
            "forms": parameters.get_admin_forms
        })
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def saveparameters(request):
    for formdef in parameters.get_admin_forms(request.POST):
        form = formdef["form"]
        if form.is_valid():
            form.save()
            form.to_django_settings()
            continue
        return render_to_json_response(
            {'form_errors': form.errors, 'prefix': form.app}, status=400
        )
    return render_to_json_response(_("Parameters saved"))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def viewextensions(request, tplname='core/extensions.html'):
    from modoboa.core.extensions import exts_pool

    exts = exts_pool.list_all()
    for ext in exts:
        try:
            dbext = Extension.objects.get(name=ext["id"])
            ext["selection"] = dbext.enabled
        except Extension.DoesNotExist:
            dbext = Extension()
            dbext.name = ext["id"]
            dbext.enabled = False
            dbext.save()
            ext["selection"] = False

    tbl = ExtensionsTable(request, exts)
    return render_to_json_response({
        "content": _render_to_string(request, tplname, {"extensions": tbl})
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def saveextensions(request):
    actived_exts = Extension.objects.filter(enabled=True)
    found = []
    for k in request.POST.keys():
        if k.startswith("select_"):
            parts = k.split("_", 1)
            dbext = Extension.objects.get(name=parts[1])            
            if not dbext in actived_exts:
                dbext.on()
            else:
                found += [dbext]
    for ext in actived_exts:
        if not ext in found:
            ext.off()

    return render_to_json_response(_("Modifications applied."))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def information(request, tplname="core/information.html"):
    return render_to_json_response({
        "content": render_to_string(tplname, {})
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def logs(request, tplname="core/logs.html"):
    from modoboa.lib.templatetags.lib_tags import pagination_bar

    sort_order, sort_dir = get_sort_order(
        request.GET, "date_created",
        allowed_values=['date_created', 'level', 'logger', 'message']
    )
    page = get_listing_page(
        Log.objects.all().order_by("%s%s" % (sort_dir, sort_order)),
        request.GET.get("page", 1)
    )
    return render_to_json_response({
        "content": render_to_string(tplname, {
            "logs": page.object_list,
        }),
        "page": page.number,
        "paginbar": pagination_bar(page),
    })
