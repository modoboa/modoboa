# -*- coding: utf-8 -*-

"""
Graphical statistics about emails traffic using RRDtool

This module provides support to retrieve statistics from postfix log :
sent, received, bounced, rejected

"""
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.conf.urls.defaults import *
from mailng.lib import events, parameters

def infos():
    return {
        "name" : "Statistics",
        "version" : "1.0",
        "description" : _("Graphical statistics about emails traffic using RRDtool")
        }

def init():
    events.register("AdminMenuDisplay", menu)
    parameters.register_admin("stats", "LOGFILE", type="string", 
                              deflt="/var/log/mail.log",
                              help=_("Path to log file used to collect statistics"))
    parameters.register_admin("stats", "RRD_ROOTDIR", type="string", 
                              deflt="/tmp/mailng",
                              help=_("Path to directory where RRD files are stored"))
    parameters.register_admin("stats", "IMG_ROOTDIR", type="string", 
                              deflt="/tmp/mailng",
                              help=_("Path to directory where PNG files are stored"))

def destroy():
    events.unregister("AdminMenuDisplay", menu)

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
