# -*- coding: utf-8 -*-
import time
from django.template.loader import render_to_string
from mailng.lib import _render

class MBconnector(object):
    def __init__(self, address, port):
        self.address = address
        self.port = port

class Page(object):
    def __init__(self, pageid, id_start, id_stop, items, 
                 items_per_page, has_previous, has_next):
        self.pageid = pageid
        self.id_start = id_start
        self.id_stop = id_stop
        self.items = items
        self.items_per_page = items_per_page
        self.has_previous = has_previous
        self.has_next = has_next

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

    def _indexes(self, page):
        id_start = self.elems_per_page * page + 1
        id_stop = id_start + self.elems_per_page - 1
        return (id_start, id_stop)
        
    def getpage(self, page):
        if page < 1:
            return None
        id_start, id_stop = self._indexes(page - 1)
        has_previous = has_next = False
        if id_start < self.total:
            if page > 1:
                has_previous = True
            if id_stop < self.total:
                has_next = True
            else:
                id_stop = self.total
        else:
            return None
        return Page(page, id_start, id_stop, self.total,
                    self.elems_per_page, has_previous, has_next)

class EmailListing:
    def __init__(self, folder=None, elems_per_page=40, **kwargs):
        self.folder = folder
        self.elems_per_page = elems_per_page
        self.paginator = Paginator(self.mbc.messages_count(self.folder), 
                                   elems_per_page)

    def render_navbar(self, page):
        return render_to_string("common/navbar.html", {
                "page" : page
                })
    
    def getfolders(self):
        return None

    def render(self, request, pageid=1, **kwargs):
        page = self.paginator.getpage(pageid)
        if not page:
            listing = "Empty folder"
        else:
            listing = self.fetch(page.id_start, page.id_stop).render(request)
        elapsed = kwargs.has_key("start") and time.time() - kwargs["start"] or 0
        return _render(request, self.tpl, {
                "listing" : listing, "elapsed" : elapsed,
                "navbar" : self.render_navbar(page),
                "folders" : self.getfolders(),
                "selection" : self.folder,
                "current_page" : pageid
                })
