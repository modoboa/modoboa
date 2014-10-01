# -*- coding: utf-8 -*-
from django.conf import settings
from django.template.loader import render_to_string
from django.template import Template, Context
from django.utils.translation import ugettext as _

from modoboa.lib.paginator import Paginator


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
