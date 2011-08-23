# -*- coding: utf-8 -*-
import time
import re
import os
import time, random, hashlib
import lxml.html
from lxml import etree
from django.conf import settings
from django.template.loader import render_to_string
from django.template import Template, Context
from django.utils.translation import ugettext as _
from modoboa.lib import _render, decode

attached_map = {}

class MBconnector(object):
    def __init__(self, address, port):
        self.address = address
        self.port = port

    def messages_count(self, **kwargs):
        pass

class Page(object):
    def __init__(self, pageid, id_start, id_stop, items, 
                 items_per_page, has_previous, has_next,
                 baseurl=None):
        self.pageid = pageid
        self.id_start = id_start
        self.id_stop = id_stop
        self.items = items
        self.items_per_page = items_per_page
        self.has_previous = has_previous
        self.has_next = has_next
        self.baseurl = baseurl

    def previous_page(self):
        if not self.has_previous:
            return False
        return self.pageid - 1

    def next_page(self):
        if not self.has_next:
            return False
        return self.pageid + 1

    def last_page(self):
        lid = self.items / self.items_per_page
        if not lid:
            return 1
        if self.items % self.items_per_page:
            lid += 1
        return lid

class Paginator(object):
    def __init__(self, total, elems_per_page):
        self.total = total
        self.elems_per_page = elems_per_page
        self.baseurl = None

    def _indexes(self, page):
        id_start = self.elems_per_page * page + 1
        id_stop = id_start + self.elems_per_page - 1
        return (id_start, id_stop)
        
    def getpage(self, page):
        if page < 1:
            return None
        id_start, id_stop = self._indexes(page - 1)
        has_previous = has_next = False
        if id_start <= self.total:
            if page > 1:
                has_previous = True
            if id_stop < self.total:
                has_next = True
            else:
                id_stop = self.total
        else:
            return None
        p = Page(page, id_start, id_stop, self.total,
                 self.elems_per_page, has_previous, has_next)
        if self.baseurl:
            p.baseurl = self.baseurl
        return p

class EmailListing(object):
    def __init__(self, baseurl=None, folder=None, elems_per_page=40, 
                 navparams={}, **kwargs):
        self.folder = folder
        self.elems_per_page = elems_per_page
        self.navparams = navparams
        self.extravars = {}
        self.empty = "empty" in kwargs.keys() and kwargs["empty"] or False
        if not self.empty:
            if kwargs.has_key("order"):
                order = kwargs["order"]
            elif self.navparams.has_key("order"):
                order = self.navparams["order"]
            else:
                order = None
            self.paginator = Paginator(self.mbc.messages_count(folder=self.folder, 
                                                               order=order), 
                                       elems_per_page)
            if baseurl:
                self.paginator.baseurl = baseurl

    @staticmethod
    def render_navbar(page):
        if page is None:
            return ""
        context = {"page" : page, "MEDIA_URL" : settings.MEDIA_URL}
        return render_to_string("common/navbar.html", context)
    
    def fetch(self, request, id_start, id_stop):
        table = self.tbltype(request,
                             self.mbc.fetch(start=id_start, stop=id_stop, 
                                            folder=self.folder, 
                                            nbelems=self.elems_per_page))
        tpl = Template("""
<form method="POST" id="listingform">
  {{ table }}
</form>""")
        return tpl.render(Context({"table" : table.render()}))

    def render(self, request, pageid=1, **kwargs):
        listing = ""
        page = None
        if not self.empty:
            page = self.paginator.getpage(pageid)
            if not page:
                listing = _("This folder contains no messages")
            else:
                listing = self.fetch(request, page.id_start, page.id_stop)
        elapsed = kwargs.has_key("start") and time.time() - kwargs["start"] or 0
        context = {
            "listing" : listing, 
            "elapsed" : elapsed,
            "navbar" : self.render_navbar(page),
            "selection" : self.folder,
            "navparams" : self.navparams,
            "deflocation" : self.deflocation, 
            "defcallback" : self.defcallback,
            "reset_wm_url" : self.reset_wm_url
            }
        for k, v in self.extravars.iteritems():
            context[k] = v
        return _render(request, self.tpl, context)

def parse_search_parameters(request):
    if request.GET.has_key("pattern"):
        request.session["pattern"] = re.escape(request.GET["pattern"])
        if request.GET.has_key("criteria"):
            request.session["criteria"] = request.GET["criteria"]
        else:
            request.session["criteria"] = ["from_addr"]
    else:
        for p in ["pattern", "criteria"]:
            if p in request.session.keys():
                del request.session[p]
    
