# -*- coding: utf-8 -*-
import time
import re
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
        if id_start < self.total:
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
    def __init__(self, folder=None, elems_per_page=40, navparams={}, **kwargs):
        self.folder = folder
        self.elems_per_page = elems_per_page
        self.navparams = navparams
        order = "order" in kwargs.keys() and kwargs["order"] or None
        self.paginator = Paginator(self.mbc.messages_count(folder=self.folder, 
                                                           order=order), 
                                   elems_per_page)

    def render_navbar(self, page):
        return render_to_string("common/navbar.html", {
                "page" : page
                })
    
    def getfolders(self):
        return None

    def fetch(self, request, id_start, id_stop):
        table = self.tbltype(self.mbc.fetch(start=id_start, stop=id_stop, 
                                            folder=self.folder))
        tpl = Template("""
<form method="POST" id="listingform">
  {{ table }}
</form>""")
        return tpl.render(Context({"table" : table.render(request)}))

    def render(self, request, pageid=1, **kwargs):
        page = self.paginator.getpage(pageid)
        thead = listing = ""
        if "empty" in kwargs.keys() and not kwargs["empty"]:
            if not page:
                listing = "Empty folder"
            else:
                listing = self.fetch(request, page.id_start, page.id_stop)
        elapsed = kwargs.has_key("start") and time.time() - kwargs["start"] or 0
        return _render(request, self.tpl, {
                "listing" : listing, 
                "elapsed" : elapsed,
                "navbar" : self.render_navbar(page),
                "folders" : self.getfolders(),
                "selection" : self.folder,
                "navparams" : self.navparams,
                "current_page" : pageid
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
            if part.get_content_type() in ("text/html", "text/plain"):
                contents[part.get_content_subtype()] += part.get_payload(decode=True)
            if mode != "html" or links == "0":
                continue

            if part.get_content_maintype() == "image":
                if part.has_key("Content-Location"):
                    fname = part["Content-Location"]
                    if re.match("^http:", fname):
                        path = fname
                    else:
                        path = "/%s" % os.path.join("static/tmp", fname)
                        fp = open(path, "wb")
                        fp.write(part.get_payload(decode=True))
                        fp.close()
                    m = re.match("<(.+)>", part["Content-ID"])
                    if m:
                        self.attached_map[m.group(1)] = path
                    else:
                        self.attached_map[part["Content-ID"]] = path

        if not contents.has_key(mode) or contents[mode] == "":
            if mode == "html":
                mode = "plain"
            else:
                mode = "html"
        self.pre, self.body = \
            getattr(self, "viewmail_%s" % mode)(contents[mode], links=links)

    def map_cid(self, url):
        import re

        map = globals()["attached_map"]
        m = re.match(".*cid:([^\"]+)", url)
        if m:
            if map.has_key(m.group(1)):
                return map[m.group(1)]
        return url

    def render_headers(self, folder, mail_id):
        attachments = []
        for part in self.attachments:
            decoded = decode_header(part.get_filename())
            if decoded[0][1] is None:
                attachments += [decoded[0][0]]
            else:
                attachments += [unicode(decoded[0][0], decoded[0][1])]
        return render_to_string("webmail/headers.html", {
                "headers" : self.headers,
                "folder" : folder, "mail_id" : mail_id,
                "attachments" : attachments != [] and attachments or None
                })
        
    def render(self, request):
        return  _render(request, 'common/getmailcontent.html', {
                "body" : self.body, "pre" : self.pre
                })

    def viewmail_plain(self, content, **kwargs):
        body = decode(content)
        return (True, body)

    def viewmail_html(self, content, **kwargs):
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
        body = Template(decode(body)).render({})
        return (False, body)

