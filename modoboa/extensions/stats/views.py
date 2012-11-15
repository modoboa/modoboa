# coding: utf-8
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.lib.webutils import _render, _render_to_string, ajax_simple_response
from modoboa.admin.models import Domain, Mailbox
from django.contrib.auth.decorators \
    import login_required, user_passes_test, permission_required
from modoboa.extensions.stats.grapher import *
from modoboa.lib.exceptions import *
from modoboa.lib import events
from graph_templates import *

periods = [{"name" : "day", "label" : ugettext_lazy("Day")},
           {"name" : "week", "label" : ugettext_lazy("Week")},
           {"name" : "month", "label" : ugettext_lazy("Month")},
           {"name" : "year", "label" : ugettext_lazy("Year")}]

@login_required
@permission_required("admin.view_mailboxes")
def index(request):
    """
    FIXME: how to select a default graph set ?
    """
    deflocation = "graphs/?gset=mailtraffic"
    if not request.user.is_superuser:
        if len(request.user.get_domains()):
            deflocation += "&searchquery=%s" % request.user.get_domains()[0].name
        else:
            raise ModoboaException(_("No statistics available"))
        
    period = request.GET.get("period", "day")
    graph_sets = events.raiseDictEvent('GetGraphSets')
    return _render(request, 'stats/index.html', {
            "periods" : periods,
            "period" : period,
            "selection" : "stats",
            "deflocation" : deflocation,
            "graph_sets" : graph_sets
            })

@login_required
@user_passes_test(lambda u: u.group != "SimpleUsers")
def graphs(request):
    gset = request.GET.get("gset", None)
    gsets = events.raiseDictEvent("GetGraphSets")
    if not gset in gsets:
        raise ModoboaException(_("Unknown graphic sets"))
    searchq = request.GET.get("searchquery", None)
    period = request.GET.get("period", "day")
    tplvars = dict(graphs=[], period=period)
    if searchq in [None, "global"]:
        if not request.user.is_superuser:
            raise PermDeniedException
        tplvars.update(domain="global")
    else:
        domain = Domain.objects.filter(name__contains=searchq)
        if len(domain) != 1:
            return ajax_simple_response({"status" : "ok"})
        if not request.user.can_access(domain[0]):
            raise PermDeniedException
        tplvars.update(domain=domain[0].name)

    if period == "custom":
        if not request.GET.has_key("start") or not request.GET.has_key("end"):
            raise ModoboaException(_("Bad custom period"))
        start = request.GET["start"]
        end = request.GET["end"]
        G = Grapher()
        period_name = "%s_%s" % (start.replace('-',''), end.replace('-',''))
        for tpl in gsets[gset].get_graphs():
            tplvars['graphs'].append(tpl.display_name)
            G.process(tplvars["domain"], period_name, str2Time(*start.split('-')),
                      str2Time(*end.split('-')), tpl)
        tplvars["period_name"] = period_name
        tplvars["start"] = start
        tplvars["end"] = end
    else:
        tplvars['graphs'] = gsets[gset].get_graph_names()

    return ajax_simple_response(dict(
            status="ok",  
            content=_render_to_string(request, "stats/graphs.html", tplvars)
            ))
