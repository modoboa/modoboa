# -*- coding: utf-8 -*-

"""Views available to super administrators only."""

from __future__ import unicode_literals

from functools import reduce

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from modoboa.core.models import Log
from modoboa.core.utils import check_for_updates
from modoboa.lib.listing import get_listing_page, get_sort_order
from modoboa.lib.web_utils import render_to_json_response
from modoboa.parameters import tools as param_tools
from .. import signals


@login_required
@user_passes_test(lambda u: u.is_superuser)
def viewsettings(request, tplname="core/settings_header.html"):
    return render(request, tplname, {
        "selection": "settings"
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def parameters(request, tplname="core/parameters.html"):
    """View to display and save global parameters."""
    if request.method == "POST":
        forms = param_tools.registry.get_forms(
            "global", request.POST, localconfig=request.localconfig)
        for formdef in forms:
            form = formdef["form"]
            if form.is_valid():
                form.save()
                form.to_django_settings()
                continue
            return render_to_json_response(
                {"form_errors": form.errors, "prefix": form.app}, status=400
            )
        request.localconfig.save()
        return render_to_json_response(_("Parameters saved"))
    return render_to_json_response({
        "left_selection": "parameters",
        "content": render_to_string(tplname, {
            "forms": param_tools.registry.get_forms(
                "global", localconfig=request.localconfig)
        }, request)
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def information(request, tplname="core/information.html"):
    status, extensions = check_for_updates(request)
    return render_to_json_response({
        "content": render_to_string(tplname, {
            "update_avail": status,
            "extensions": extensions,
        }),
    })


def get_logs_page(request, page_id=None):
    """Return a page of logs."""
    sort_order, sort_dir = get_sort_order(
        request.GET, "date_created",
        allowed_values=["date_created", "level", "logger", "message"]
    )
    if page_id is None:
        page_id = request.GET.get("page", None)
        if page_id is None:
            return None
    return get_listing_page(
        Log.objects.all().order_by("%s%s" % (sort_dir, sort_order)),
        page_id
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def logs(request, tplname="core/logs.html"):
    """Return a list of log entries.

    This view is only called the first time the page is displayed.

    """
    page = get_logs_page(request, 1)
    return render_to_json_response({
        "callback": "logs",
        "content": render_to_string(tplname, {"logs": page.object_list}),
        "page": page.number
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def logs_page(request, tplname="core/logs_page.html"):
    """Return a page containing logs."""
    page = get_logs_page(request)
    if page is None:
        context = {"length": 0}
    else:
        context = {
            "rows": render_to_string(tplname, {"logs": page.object_list}),
            "pages": [page.number]
        }
    return render_to_json_response(context)


@login_required
def check_top_notifications(request):
    """AJAX service to check for new top notifications to display."""
    notifications = signals.get_top_notifications.send(
        sender="top_notifications", include_all=True)
    notifications = reduce(
        lambda a, b: a + b, [notif[1] for notif in notifications])
    return render_to_json_response(notifications)
