# -*- coding: utf-8 -*-

"""
graph plugin do display rrd stats

This module provides rrdtool support to retreive statistics
from postfix log : sent, received, bounced, rejected

"""
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.conf.urls.defaults import *
from mailng.lib import events, parameters, _render
from mailng.admin.views import good_domain
from mailng.admin.models import Domain, Mailbox
from django.contrib.auth.decorators \
    import login_required, user_passes_test, permission_required

graph_types = ['AVERAGE', 'MAX']

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
            {"name"  : _("Statistics"),
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
        "domain":domain,"domains" : domains, "messages" : errors ,
        "types" :  graph_type, "tmp_path" : tmp_path})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def adminindex(request):
    period = request.GET.has_key("period") and request.GET["period"] or "day"
    domain = request.GET.has_key("domain") and request.GET["domain"] or "global"
    if domain != "global":
        domain = Domain.objects.get(pk=domain)
        domain = domain.name
    domains = Domain.objects.all()
    return _render(request, 'stats/adminindex.html', {
            "domains" : domains, "domain" : domain,
            "graphs" : [{"name" : "traffic", "label" : _("Average normal traffic")},
                        {"name" : "badtraffic", "label" : _("Average bad traffic")},
                        {"name" : "size", "label" : _("Average normal traffic size")}],
            "periods" : ["day", "week", "month", "year"],
            "period" : period
            })

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
            "graphs" : [{"name" : "traffic", "label" : _("Average normal traffic")},
                        {"name" : "badtraffic", "label" : _("Average bad traffic")},
                        {"name" : "size", "label" : _("Average normal traffic size")}],
            "periods" : ["day", "week", "month", "year"],
            "period" : period
            })
