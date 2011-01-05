# -*- coding: utf-8 -*-

"""
Graphical statistics about emails traffic using RRDtool

This module provides support to retrieve statistics from postfix log :
sent, received, bounced, rejected

"""
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.conf.urls.defaults import *
from modoboa.lib import events, parameters, static_url

def infos():
    return {
        "name" : "Statistics",
        "version" : "1.0",
        "description" : _("Graphical statistics about emails traffic using RRDtool")
        }

def init():
    events.register("AdminMenuDisplay", menu)
    parameters.register_admin("LOGFILE", type="string", 
                              deflt="/var/log/mail.log",
                              help=_("Path to log file used to collect statistics"))
    parameters.register_admin("RRD_ROOTDIR", type="string", 
                              deflt="/tmp/modoboa",
                              help=_("Path to directory where RRD files are stored"))
    parameters.register_admin("IMG_ROOTDIR", type="string", 
                              deflt="/tmp/modoboa",
                              help=_("Path to directory where PNG files are stored"))

def destroy():
    events.unregister("AdminMenuDisplay", menu)

def urls(prefix):
    return (r'^%sstats/' % prefix, 
            include('modoboa.extensions.stats.urls'))

def menu(**kwargs):
    if kwargs["target"] == "admin_menu_box":
        return [
            {"name"  : "stats",
             "label" : _("Statistics"),
             "url" : reverse('fullindex'),
             "img" : static_url("pics/graph.png")}
            ]
    return []
