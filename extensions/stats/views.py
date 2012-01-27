# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _, ugettext_noop
from django.utils import simplejson
from modoboa.lib.webutils import _render, _render_to_string, getctx
from modoboa.admin.lib import check_domain_access
from modoboa.admin.models import Domain, Mailbox
from django.contrib.auth.decorators \
    import login_required, user_passes_test, permission_required
from modoboa.extensions.stats.grapher import *

graph_types = ['AVERAGE', 'MAX']
graph_list = [{"name" : "traffic", "label" : ugettext_noop("Average normal traffic")},
              {"name" : "badtraffic", "label" : ugettext_noop("Average bad traffic")},
              {"name" : "size", "label" : ugettext_noop("Average normal traffic size")}]
periods = [{"name" : "day", "label" : ugettext_noop("Day")},
           {"name" : "week", "label" : ugettext_noop("Week")},
           {"name" : "month", "label" : ugettext_noop("Month")},
           {"name" : "year", "label" : ugettext_noop("Year")},
           {"name" : "custom", "label" : ugettext_noop("Custom")}]

@login_required
@permission_required("admin.view_mailboxes")
@check_domain_access
def index(request):
    domains = None
    period = request.GET.get("period", "day")
    domid = request.GET.get("domid", "")

    domains = request.user.get_domains()

    return _render(request, 'stats/index.html', {
            "domains" : domains,
            "graphs" : graph_list,
            "periods" : periods,
            "period" : period,
            "selection" : "stats",
            "domid" : domid
            })

@login_required
@permission_required("admin.view_mailboxes")
def getgraph(request, dom_id):
    period = request.GET.get("period", "day")
    if dom_id == "global":
        if not request.user.is_superuser:
            raise PermDeniedError(_("you're not allowed to see those statistics"))
        domain = dom_id
    else:
        domain = Domain.objects.get(pk=dom_id)
        if not request.user.can_access(domain):
            raise PermDeniedError(_("You don't have access to this domain"))

    ctx = None
    tplvars = {"graphs" : graph_list, "period" : period, "domain" : domain.name}
    if period == "custom":
        if not request.GET.has_key("start") or not request.GET.has_key("end"):
            ctx = getctx("ko", error=_("Bad custom period"))
        else:
            start = request.GET["start"]
            end = request.GET["end"]
            G = Grapher()
            period_name = "%s_%s" % (start.replace('-',''), end.replace('-',''))
            for tpl_name in graph_list:
                G.process(domain.name,
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
