# -*- coding: utf-8 -*-

"""
graph plugin do display rrd stats

This module provides rrdtool support to retreive statistics
from postfix log : sent, received, bounced, rejected

"""
import calendar
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.conf.urls.defaults import *
from mailng.lib import events, parameters, _render
from mailng.admin.views import good_domain
from mailng.admin.models import Domain, Mailbox
from django.contrib.auth.decorators \
    import login_required, user_passes_test, permission_required
from extensions.stats.grapher import Grapher, tpl
from extensions.stats.logparser import str2Time

graph_types = ['AVERAGE', 'MAX']

graph_list = [{"name" : "traffic", "label" : _("Average normal traffic")},
              {"name" : "badtraffic", "label" : _("Average bad traffic")},
              {"name" : "size", "label" : _("Average normal traffic size")}]

def init():
    events.register("AdminMenuDisplay", menu)
    parameters.register("stats", "LOGFILE", "string", "/var/log/mail.log",
                        help=_("Path to log file used to collect statistics"))
    parameters.register("stats", "RRD_ROOTDIR", "string", "/tmp/mailng",
                        help=_("Path to directory where RRD files are stored"))
    parameters.register("stats", "IMG_ROOTDIR", "string", "/tmp/mailng",
                        help=_("Path to directory where PNG files are stored"))

def urls():
    return (r'^mailng/stats/', 
            include('mailng.extensions.stats.urls'))

def menu(**kwargs):
    if kwargs["target"] == "admin_menu_bar":
        domain_id = kwargs['domain']
        return [
            {"label" : _("Statistics"),
             "name"  : "stats",
             "url" : reverse('domindex', args=[domain_id]),
             "img" : "/static/pics/graph.png"}
            ]
    if kwargs["target"] == "admin_menu_box":
        return [
            {"name"  : "stats",
             "label" : _("Statistics"),
             "url" : reverse('fullindex'),
             "img" : "/static/pics/graph.png"}
            ]
    return []

@login_required
def domain(request,dom_id):
    domains = []
    errors = []
    return graph_display(request,dom_id,graph_types)

@login_required
def graph_display(request,dom_id,graph_t=graph_types):
    domains = []
    errors = []
    graph_type = None
    domain=None
    if type(graph_t) == type([]):
        graph_type = graph_t
    else :
        graph_type = [graph_t]

    if dom_id:
        domain = Domain.objects.get(pk=dom_id)
        if domain:
            domains.append(domain)

    if domains == []:
        errors.append(_("No Domain defined"))


    for d in domains:
        P = parser(d.name)
        if type(P) == type('err'):
            errors.append(P)
        else:
            P.plot_rrd()

    return _render(request, 'stats/index.html', {
        "page" : "Domain statistics", "graph"   : graph_nature,
        "domain": domain, "domains" : domains, "messages" : errors,
        "types" : graph_type, "tmp_path" : tmp_path,
        "img_rootdir" : parameters.get("stats", "IMG_ROOTDIR")})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def adminindex(request):
    CH = calendar.HTMLCalendar(calendar.MONDAY)
    CH_print = CH.formatmonth(2009,11)
    period = request.GET.has_key("period") and request.GET["period"] or "day"
    domain = request.GET.has_key("domain") and request.GET["domain"] or "global"
    if domain != "global":
        domain = Domain.objects.get(pk=domain)
        domain = domain.name
    domains = Domain.objects.all()
    G = Grapher()
    for name, t in tpl.iteritems():
        G.make_defaults(domain, t)

    return _render(request, 'stats/adminindex.html', {
        "domains" : domains, "domain" : domain,
        "graphs" : graph_list,
        "periods" : ["day", "week", "month", "year","Custom"],
        "period" : period, "cal" : CH_print,
        "img_rootdir" : parameters.get("stats", "IMG_ROOTDIR")})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def custom_period(request):
    start = None
    end = None
    start_ref = None
    end_ref = None
    domains = Domain.objects.all()
    domain = request.GET.has_key("domain") and request.GET["domain"] or "global"
    period = request.GET.has_key("period") and request.GET["period"] or "Custom"

    if domain != "global":
        domain = Domain.objects.get(pk=domain)
        domain = domain.name
    try:
        start_ref = str(request.POST.get('start'))
        start = start_ref.split(', ')[1]
        end_ref = str(request.POST.get('end'))
        end = end_ref.split(', ')[1]
    except:
        pass

    if not end or not start:
        return _render(request, 'stats/adminindex.html', {
            "domains" : domains, "domain" : domain,
            "graphs" : graph_list,
            "period" : period,
            "periods" : ["day", "week", "month", "year","Custom"],
            "period_name":None,
            "start" : start_ref,
            "end" : end_ref,
            "messages" : ["Custom period not selected"],
            "img_rootdir" : parameters.get("stats", "IMG_ROOTDIR")})

    period_name = "%s_%s" %(start.replace('/',''),end.replace('/',''))
    G = Grapher()
    for tpl_name in graph_list:
        G.process(domain,
                  period_name,
                  str2Time(*start.split('/')),
                  str2Time(*end.split('/')),
                  tpl[tpl_name['name']])

    print "[stats] ", period
    return _render(request, 'stats/adminindex.html', {
        "domains" : domains, "domain" : domain,
        "graphs" : graph_list,
        "period" : period,
        "periods" : ["day", "week", "month", "year","Custom"],
        "period_name": period_name,
        "start" : start_ref,
        "end" : end_ref,
        "messages" : None,
        "img_rootdir" : parameters.get("stats", "IMG_ROOTDIR")})


@login_required
@good_domain
@permission_required("admin.view_mailboxes")
def index(request, dom_id=None):
    domain = None
    period = request.GET.has_key("period") and request.GET["period"] or "day"
    if request.user.has_perm("admin.view_mailboxes"):
        domain = Domain.objects.get(pk=dom_id)

    return _render(request, 'stats/index.html', {
        "domain" : domain,
        "graphs" : graph_list,
        "periods" : ["day", "week", "month", "year","Custom"],
        "period" : period,
        "img_rootdir" : parameters.get("stats", "IMG_ROOTDIR")})
