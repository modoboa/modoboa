# -*- coding: utf-8 -*-
import re
from django.conf import settings
from django.template.loader import render_to_string
from django.template import Template, Context
from django.utils.translation import ugettext as _

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
        self.number = pageid
        self.id_start = id_start
        self.id_stop = id_stop
        self.items = items
        self.items_per_page = items_per_page
        self.has_previous = has_previous
        self.has_next = has_next
        self.baseurl = baseurl

    def previous_page_number(self):
        if not self.has_previous:
            return False
        return self.number - 1

    def next_page_number(self):
        if not self.has_next:
            return False
        return self.number + 1

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
        self.num_pages = total / elems_per_page
        if total % elems_per_page:
            self.num_pages += 1

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
        p.paginator = self
        return p


class EmailListing(object):

    def __init__(self, baseurl=None, folder=None, elems_per_page=40, 
                 navparams={}, **kwargs):
        self.folder = folder
        self.elems_per_page = elems_per_page
        self.navparams = navparams
        self.extravars = {}
        self.show_listing_headers = False
        self.empty = "empty" in kwargs and kwargs["empty"] or False
        if self.empty:
            return
        if "order" in kwargs:
            order = kwargs["order"]
        elif "order" in self.navparams:
            order = self.navparams["order"]
        else:
            order = None
        self.paginator = Paginator(
            self.mbc.messages_count(folder=self.folder, order=order),
            elems_per_page
        )
        self.baseurl = baseurl

    @staticmethod
    def render_navbar(page, baseurl=None):
        if page is None:
            return ""
        context = {
            "page": page, "STATIC_URL": settings.STATIC_URL, "baseurl": baseurl
        }
        return render_to_string("common/pagination_bar.html", context)

    def fetch(self, request, id_start, id_stop):
        table = self.tbltype(
            request,
            self.mbc.fetch(start=id_start, stop=id_stop,
                           mbox=self.folder,
                           nbelems=self.elems_per_page)
        )
        tpl = Template("""
<form method="POST" id="listingform">
  {{ table }}
</form>""")
        return tpl.render(
            Context({
                "table": table.render(withheader=self.show_listing_headers)
            })
        )

    def render(self, request, pageid=1, **kwargs):
        page = self.paginator.getpage(pageid)
        if not page:
            listing = "<div class='alert alert-info'>%s</div>" % _("Empty mailbox")
        else:
            listing = self.fetch(request, page.id_start, page.id_stop)
        return dict(listing=listing, navbar=self.render_navbar(page, self.baseurl))
