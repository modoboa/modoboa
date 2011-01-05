# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.utils import simplejson
from modoboa.lib import _render, _render_to_string, getctx
from modoboa.admin.views import good_domain
from modoboa.admin.models import Domain, Mailbox
from django.contrib.auth.decorators \
    import login_required, user_passes_test, permission_required
from modoboa.extensions.stats.grapher import *

graph_types = ['AVERAGE', 'MAX']
graph_list = [{"name" : "traffic", "label" : _("Average normal traffic")},
              {"name" : "badtraffic", "label" : _("Average bad traffic")},
              {"name" : "size", "label" : _("Average normal traffic size")}]
periods = [{"name" : "day", "label" : _("Day")},
           {"name" : "week", "label" : _("Week")},
           {"name" : "month", "label" : _("Month")},
           {"name" : "year", "label" : _("Year")},
           {"name" : "custom", "label" : _("Custom")}]

@login_required
@good_domain
@permission_required("admin.view_mailboxes")
def index(request):
    domains = None
    period = request.GET.has_key("period") and request.GET["period"] or "day"
    domid = request.GET.has_key("domid") and request.GET["domid"] or ""
    if request.user.is_superuser:
        domains = Domain.objects.all()
        domain = "global"
    else:
        domain = Domain.objects.get(pk=domid)

    return _render(request, 'stats/index.html', {
            "domains" : domains,
            "domain" : domain,
            "graphs" : graph_list,
            "periods" : periods,
            "period" : period,
            "selection" : "stats",
            "domid" : domid
            })

@login_required
@good_domain
@permission_required("admin.view_mailboxes")
def getgraph(request, dom_id):
    period = request.GET.has_key("period") and request.GET["period"] or "day"
    if dom_id == "global":
        domain = dom_id
    else:
        domain = Domain.objects.get(pk=dom_id).name
    ctx = None
    tplvars = {"graphs" : graph_list, "period" : period, "domain" : domain}
    if period == "custom":
        if not request.GET.has_key("start") or not request.GET.has_key("end"):
            ctx = getctx("ko", error=_("Bad custom period"))
        else:
            start = request.GET["start"]
            end = request.GET["end"]
            G = Grapher()
            period_name = "%s_%s" % (start.replace('-',''), end.replace('-',''))
            for tpl_name in graph_list:
                G.process(domain,
                          period_name,
                          str2Time(*start.split('-')),
                          str2Time(*end.split('-')),
                          tpl[tpl_name['name']])
            tplvars["period_name"] = period_name
            tplvars["start"] = start
            tplvars["end"] = end
    if ctx is None:
        content = _render_to_string(request, "stats/graphs.html", tplvars)
        ctx = getctx("ok", content=content)

    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
