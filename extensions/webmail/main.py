# -*- coding: utf-8 -*-
import time
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.conf.urls.defaults import include
from django.contrib.auth.decorators import login_required
from mailng.admin.models import Mailbox
from mailng.lib import events, parameters
from mailng.lib import _render
from imap_listing import *

def init():
    events.register("UserMenuDisplay", menu)
    events.register("UserLogin", userlogin)
    parameters.register("webmail", "SERVER_ADDRESS", "string", "127.0.0.1",
                        help=_("Mailboxes server address"))

def urls():
    return (r'^mailng/webmail/',
            include('mailng.extensions.webmail.urls'))

def menu(**kwargs):
    if kwargs["target"] != "user_menu_box":
        return []
    return [
        {"name" : _("Webmail"),
         "url" : reverse(folder),
         "img" : "/static/pics/webmail.png"}
        ]

def userlogin(**kwargs):
    kwargs["request"].session["password"] = kwargs["password"]

@login_required
def folder(request, name=None):
    if not name:
        name = "INBOX"
    lst = ImapListing(request.user.username, request.session["password"],
                      reverse(folder, args=[name]), folder=name)
    pageid = request.GET.has_key("page") and int(request.GET["page"]) or 1
    if "mode" in request.GET.keys() and request.GET["mode"] == "ajax":
        page = lst.paginator.getpage(pageid)
        if page:
            content = lst.fetch(page.id_start, page.id_stop).render(request)
            navbar = lst.render_navbar(page)
        else:
            content = "Empty folder"
            navbar = ""
        ctx = {"status" : "ok", "listing" : content, "navbar" : navbar, 
               "menu" : "", "current_page" : pageid}
        if "menu" in request.GET.keys():
            from templatetags.webextras import listing_menu
            ctx["menu"] = listing_menu("", request.user.get_all_permissions())
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
    return lst.render(request, pageid=int(pageid))

def fetchmail(request, folder, mail_id, all=False):
    mbc = IMAPconnector(parameters.get("webmail", "SERVER_ADDRESS"), 143)
    mbc.login(request.user.username, request.session["password"])
    res = mbc.fetch(start=mail_id, folder=folder, all=all)
    if len(res):
        return res[0]
    return None

@login_required
def viewmail(request, folder, mail_id=None):
    header = fetchmail(request, folder, mail_id)
    pageid = request.GET.has_key("page") and request.GET["page"] or "1"
    if header:
        from templatetags.webextras import viewm_menu
        menu = viewm_menu("", folder, mail_id, pageid,
                          request.user.get_all_permissions())
        folder, imapid = header["imapid"].split("/")
        mailcontent = render_to_string("webmail/viewmail.html", {
                "header" : header, "folder" : folder, "imapid" : imapid
                })
        ctx = {"status" : "ok", "menu" : menu, "mailcontent" : mailcontent}
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
#         return _render(request, "webmail/viewmail.html", {
#                 "header" : header, "folder" : folder, "pageid" : pageid,
#                 "menu" : menu
#                 })

@login_required
def getmailcontent(request, folder, mail_id):
    from mailng.lib.email_listing import Email

    msg = fetchmail(request, folder, mail_id, True)
    email = Email(msg)
    return email.render(request)
