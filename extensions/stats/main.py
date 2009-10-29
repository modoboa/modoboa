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
from mailng.extensions.stats.mailrrd import parser
from django.contrib.auth.decorators \
    import login_required
#from models import Stats
import pdb

graph_nature = ["sent_recv","boun_reje"]
graph_types  = ["AVERAGE","MAX"]
tmp_path     = "static/tmp"

def init():
    events.register("UserMenuDisplay", menu)

def urls():
    return (r'^mailng/stats/', 
            include('mailng.extensions.stats.urls'))


def menu(**kwargs):
    if kwargs["target"] != "user_menu_box":
        return []

    return [
        {"name" : _("Statistics"),
         "url" : reverse(index),
         "img" : "/static/pics/graph.png"}
        ]

@login_required
def domain(request,dom_id):
    domains = []
    errors = []
    return graph_display(request,dom_id,graph_types)

#@login_required
def graph_display(request,dom_id,graph_t):
    domains = []
    errors = []
    graph_type = None
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
        P.plot_rrd()

    return _render(request, 'stats/index.html', {
        "page" : "Domain statistics", "graph"   : graph_nature,
        "domains" : domains, "messages" : "graph display" ,
        "types" :  graph_type, "tmp_path" : tmp_path})


@login_required
def index(request, message=None):
    domains = []
    errors = []
    if not is_superuser(request.user):
        if not request.user.has_perm("admin.view_domains"):
            if request.user.has_perm("admin.view_mailboxes"):
                mb = Mailbox.objects.get(user=request.user.id)
                dom_id=mb.domain.id
                domain = Domain.objects.get(pk=dom_id)
                if domain:
                    domains.append(domain)
    else:
        domains = Domain.objects.all()

    if domains == []:
        errors.append(_("No Domain defined"))
    return _render(request, 'stats/index.html', {
        "page" : "Statistics",
        "domains" : domains, "messages" : errors ,"types" : graph_types})
