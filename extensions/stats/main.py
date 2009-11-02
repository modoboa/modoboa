# -*- coding: utf-8 -*-

"""
graph plugin do display rrd stats

This module provides rrdtool support to retreive statistics
from postfix log : sent, received, bounced, rejected

"""
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.conf.urls.defaults import *
from mailng.lib import events, _render
from mailng.admin.views import is_superuser
from mailng.admin.models import Domain, Mailbox
#from mailng.extensions.stats.mailrrd import parser
from django.contrib.auth.decorators \
    import login_required
import pdb

graph_nature = ["sent_recv","boun_reje"]
graph_types  = ["AVERAGE","MAX"]
tmp_path     = "static/tmp"

def init():
        events.register("AdminMenuDisplay", menu)

def urls():
    return (r'^mailng/stats/', 
            include('mailng.extensions.stats.urls'))


def menu(**kwargs):
    print kwargs
    domain_id = kwargs['domain']
    if kwargs["target"] == "admin_menu_bar":
        return [
            {"label" : _("Statistics"),
             "name"  : "stats",
             "url" : reverse('domindex', args=[domain_id]),
             "img" : "/static/pics/graph.png"}
            ]
    else:
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
def index(request, dom_id=None):
    domains = []
    errors = []
    domain = None
    if dom_id:
        if request.user.has_perm("admin.view_mailboxes"):
            domain = Domain.objects.get(pk=dom_id)
            if domain:
                domains.append(domain)
            else:
                print "pas de dom"
    else:
        domains = Domain.objects.all()

    if domains == []:
        errors.append(_("No Domain defined"))
    return _render(request, 'stats/index.html', {
        "page" : "Statistics",
        "domain" : domain, "domains": domains, "messages" : errors , 
        "periods" : ["day", "week", "month", "year"]
        })
