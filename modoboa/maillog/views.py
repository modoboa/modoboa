# coding: utf-8

"""Custom views."""

import re
import time

from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import (
    login_required, user_passes_test, permission_required
)

from modoboa.admin.models import Domain
from modoboa.lib.exceptions import BadRequest, NotFound
from modoboa.lib.web_utils import (
    render_to_json_response
)

from . import signals
from .lib import date_to_timestamp


@login_required
@permission_required("admin.view_mailbox")
def index(request):
    """
    FIXME: how to select a default graph set ?
    """
    deflocation = "graphs/?gset=mailtraffic"
    if not request.user.is_superuser:
        if not Domain.objects.get_for_admin(request.user).count():
            raise NotFound(_("No statistics available"))

    graph_sets = {}
    for result in signals.get_graph_sets.send(
            sender="index", user=request.user):
        graph_sets.update(result[1])
    periods = [
        {"name": "day", "label": _("Day")},
        {"name": "week", "label": _("Week")},
        {"name": "month", "label": _("Month")},
        {"name": "year", "label": _("Year")},
        {"name": "custom", "label": _("Custom")}
    ]
    return render(request, 'maillog/index.html', {
        "periods": periods,
        "selection": "stats",
        "deflocation": deflocation,
        "graph_sets": graph_sets
    })


@login_required
@user_passes_test(lambda u: u.role != "SimpleUsers")
def graphs(request):
    gset = request.GET.get("gset", None)
    graph_sets = {}
    for result in signals.get_graph_sets.send(
            sender="index", user=request.user):
        graph_sets.update(result[1])
    if gset not in graph_sets:
        raise NotFound(_("Unknown graphic set"))
    period = request.GET.get("period", "day")
    tplvars = {"graphs": {}, "period": period}
    fname = graph_sets[gset].get_file_name(request)
    if fname is None:
        raise BadRequest(_("Unknown domain"))
    tplvars["fname"] = fname

    if period == "custom":
        if "start" not in request.GET or "end" not in request.GET:
            raise BadRequest(_("Bad custom period"))
        start = request.GET["start"]
        end = request.GET["end"]
        expr = re.compile(r'[:\- ]')
        period_name = "%s_%s" % (expr.sub('', start), expr.sub('', end))
        start = date_to_timestamp(expr.split(start))
        end = date_to_timestamp(expr.split(end))
    else:
        end = int(time.mktime(time.localtime()))
        start = "-1%s" % period
        period_name = period

    tplvars["domain_selector"] = graph_sets[gset].domain_selector
    tplvars["graphs"] = graph_sets[gset].export(tplvars["fname"], start, end)
    tplvars["period_name"] = period_name
    tplvars["start"] = start
    tplvars["end"] = end

    return render_to_json_response(tplvars)


@login_required
@user_passes_test(lambda u: u.role != "SimpleUsers")
def get_domain_list(request):
    """Get the list of domains the user can see."""
    doms = []
    for dom in Domain.objects.get_for_admin(request.user):
        doms += [dom.name]
        doms += [alias.name for alias in dom.domainalias_set.all()]

    return render_to_json_response(doms)
