# coding: utf-8

"""
Graphical statistics about emails traffic using RRDtool

This module provides support to retrieve statistics from postfix log :
sent, received, bounced, rejected

"""
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _, ugettext_lazy
from django.conf.urls.defaults import *
from modoboa.lib import events, parameters
from modoboa.lib.webutils import static_url

def infos():
    return {
        "name" : "Statistics",
        "version" : "1.0",
        "description" : _("Graphical statistics about emails traffic using RRDtool"),
        "url" : "stats"
        }

def load():
    parameters.register_admin("LOGFILE", type="string", 
                              deflt="/var/log/mail.log",
                              help=ugettext_lazy("Path to log file used to collect statistics"))
    parameters.register_admin("RRD_ROOTDIR", type="string", 
                              deflt="/tmp/modoboa",
                              help=ugettext_lazy("Path to directory where RRD files are stored"))
    parameters.register_admin("IMG_ROOTDIR", type="string", 
                              deflt="/tmp/modoboa",
                              help=ugettext_lazy("Path to directory where PNG files are stored"))
    parameters.register_admin("GRAPHS_LOCATION", type="string", 
                              deflt="graphs",
                              help=ugettext_lazy("Graphics location (to build URLs)"))

def destroy():
    events.unregister("AdminMenuDisplay", menu)

@events.observe("UserMenuDisplay")
def menu(target, user):
    if target != "top_menu" or user.group == "SimpleUsers":
        return []
    return [
        {"name"  : "stats",
         "label" : _("Statistics"),
         "url" : reverse('fullindex')}
        ]
