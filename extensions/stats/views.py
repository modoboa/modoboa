# coding: utf-8
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.lib.webutils import _render, _render_to_string, ajax_simple_response
from modoboa.admin.models import Domain, Mailbox
from django.contrib.auth.decorators \
    import login_required, user_passes_test, permission_required
from modoboa.extensions.stats.grapher import *
from modoboa.lib.exceptions import *

graph_types = ['AVERAGE', 'MAX']
graph_list = [{"name" : "traffic", "label" : ugettext_lazy("Average normal traffic")},
              {"name" : "badtraffic", "label" : ugettext_lazy("Average bad traffic")},
              {"name" : "size", "label" : ugettext_lazy("Average normal traffic size")}]
periods = [{"name" : "day", "label" : ugettext_lazy("Day")},
           {"name" : "week", "label" : ugettext_lazy("Week")},
           {"name" : "month", "label" : ugettext_lazy("Month")},
           {"name" : "year", "label" : ugettext_lazy("Year")},
           {"name" : "custom", "label" : ugettext_lazy("Custom")}]

@login_required
@permission_required("admin.view_mailboxes")
def index(request):
    deflocation = ""
    if request.user.is_superuser:
        deflocation = "graphs/?view=global"
    else:
        if len(request.user.get_domains()):
            deflocation = "graphs/?view=%s" % request.user.get_domains()[0].name
        else:
            raise ModoboaException(_("No statistics available"))
        
    period = request.GET.get("period", "day")
    return _render(request, 'stats/index.html', {
            "graphs" : graph_list,
            "periods" : periods,
            "period" : period,
            "selection" : "stats",
            "deflocation" : deflocation
            })

@login_required
@user_passes_test(lambda u: u.group != "SimpleUsers")
def graphs(request):
    view = request.GET.get("view", None)
    if not view:
        raise ModoboaException(_("Invalid request"))
    period = request.GET.get("period", "day")
    tplvars = dict(graphs=graph_list, period=period, 
                   graphs_loc=parameters.get_admin("GRAPHS_LOCATION"))
    if view == "global":
        if not request.user.is_superuser:
            raise PermDeniedException
        tplvars.update(domain=view)
    else:
        try:
            domain = Domain.objects.get(name=view)
        except Domain.DoesNotExist:
            raise ModoboaException(_("Domain not found. Please enter a full name"))
        if not request.user.can_access(domain):
            raise PermDeniedException
        tplvars.update(domain=domain.name)

    if period == "custom":
        if not request.GET.has_key("start") or not request.GET.has_key("end"):
            raise ModoboaException(_("Bad custom period"))
        start = request.GET["start"]
        end = request.GET["end"]
        G = Grapher()
        period_name = "%s_%s" % (start.replace('-',''), end.replace('-',''))
        for tpl_name in graph_list:
            G.process(tplvars["domain"],
                      period_name,
                      str2Time(*start.split('-')),
                      str2Time(*end.split('-')),
                      tpl[tpl_name['name']])
        tplvars["period_name"] = period_name
        tplvars["start"] = start
        tplvars["end"] = end

    return ajax_simple_response(dict(
            status="ok", content=_render_to_string(request, "stats/graphs.html", tplvars)
            ))
