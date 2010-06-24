# -*- coding: utf-8 -*-
import time
import re
import os
import time, random, hashlib
from email.header import decode_header
import lxml
import lxml.html
from lxml import etree
from django.template.loader import render_to_string
from django.template import Template, Context
from django.utils.translation import ugettext as _
from mailng.lib import _render, decode

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

class EmailListing:
    def __init__(self, baseurl=None, folder=None, elems_per_page=40, 
                 navparams={}, **kwargs):
        self.folder = folder
        self.elems_per_page = elems_per_page
        self.navparams = navparams
        order = "order" in kwargs.keys() and kwargs["order"] or None
        self.empty = "empty" in kwargs.keys() and kwargs["empty"] or False
        if not self.empty:
            self.paginator = Paginator(self.mbc.messages_count(folder=self.folder, 
                                                               order=order), 
                                       elems_per_page)
            if baseurl:
                self.paginator.baseurl = baseurl

    def render_navbar(self, page):
        if page is None:
            return ""
        return render_to_string("common/navbar.html", {
                "page" : page
                })
    
    def fetch(self, request, id_start, id_stop):
        table = self.tbltype(self.mbc.fetch(start=id_start, stop=id_stop, 
                                            folder=self.folder))
        tpl = Template("""
<form method="POST" id="listingform">
  {{ table }}
</form>""")
        return tpl.render(Context({"table" : table.render(request)}))

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
        return _render(request, self.tpl, {
                "listing" : listing, 
                "elapsed" : elapsed,
                "navbar" : self.render_navbar(page),
                "selection" : self.folder,
                "navparams" : self.navparams,
                "deflocation" : self.deflocation, 
                "defcallback" : self.defcallback,
                "reset_wm_url" : self.reset_wm_url
                })

class Email(object):
    def __init__(self, msg, mode="plain", links="0"):
        self.attached_map = {}
        contents = {"html" : "", "plain" : ""}
        self.headers = []
        self.attachments = []
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.has_key("Content-Disposition"):
                if re.match("^attachment", part["Content-Disposition"]):
                    self.attachments += [part]
                    continue
            if part.get_content_type() == "text/calendar":
                contents["plain"] += part.get_payload(decode=True)
                continue
            if part.get_content_type() in ("text/html", "text/plain"):
                contents[part.get_content_subtype()] += part.get_payload(decode=True)
            if mode != "html" or links == "0":
                continue
            if part.get_content_maintype() == "application":
                self.attachments += [part]
                continue

            if part.get_content_maintype() == "image":
                m = re.match("<(.+)>", part["Content-ID"])
                cid = m is not None and m.group(1) or part["Content-ID"]

                if part.has_key("Content-Location"):
                    fname = part["Content-Location"]
                    if re.match("^http:", fname):
                        path = fname
                    else:
                        path = self.__save_image(fname, part)
                elif part.has_key("Content-Disposition"):
                    if not part["Content-Disposition"].startswith("inline"):
                        continue
                    params = part["Content-Disposition"].split(";")
                    fname = None
                    for p in params:
                        lst = p.strip().split("=")
                        if len(p) and p[0] == "filename":
                            fname = p[1]
                            break
                    path = self.__save_image(fname is None and cid or fname, part)
                else:
                    continue
               
                self.attached_map[cid] = path
                continue


        if not contents.has_key(mode) or contents[mode] == "":
            if mode == "html":
                mode = "plain"
            else:
                mode = "html"

        self.pre, self.body = \
            getattr(self, "viewmail_%s" % mode)(contents[mode], links=links)

    def __save_image(self, fname, part):
        if re.search("\.\.", fname):
            return None
        path = "static/tmp/" + fname
        fp = open(path, "wb")
        fp.write(part.get_payload(decode=True))
        fp.close()
        return "/" + path

    def map_cid(self, url):
        import re

        m = re.match(".*cid:(.+)", url)
        if m:
            if self.attached_map.has_key(m.group(1)):
                return self.attached_map[m.group(1)]
        return url

    def render_headers(self, **kwargs):
        return render_to_string("common/mailheaders.html", {
                "headers" : self.headers,
                })
        
    def render(self, request):
        return  _render(request, 'common/getmailcontent.html', {
                "body" : self.body, "pre" : self.pre
                })

    def viewmail_plain(self, content, **kwargs):
        body = decode(content)
        return (True, body)

    def viewmail_html(self, content, **kwargs):
        if content is None or content == "":
            return (False, "")
        links = kwargs.has_key("links") and kwargs["links"] or "0"
        html = lxml.html.fromstring(content) 
        if links == "0":
            html.rewrite_links(lambda x: None)
        else:
            html.rewrite_links(self.map_cid)
        body = html.find("body")
        if body is None:
            body = lxml.html.tostring(html)
        else:
            body = lxml.html.tostring(body)
            body = re.sub("<(/?)body", lambda m: "<%sdiv" % m.group(1), body)
        body = Template(decode(body)).render(Context({}))
        return (False, body)

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
    
