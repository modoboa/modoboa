# -*- coding: utf-8 -*-
import time
from django.http import HttpResponse
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
         "url" : reverse(index),
         "img" : "/static/pics/webmail.png"}
        ]

@login_required
def index(request):
    start = time.time()
    lst = ImapListing(request.user.username, request.session["password"])
    try:
        pageid = request.GET["page"]
    except KeyError:
        pageid = 1
    return lst.render(request, pageid=int(pageid), start=start)

@login_required
def folder(request, folder):
    lst = ImapListing(request.user.username, request.session["password"],
                      folder=folder)
    try:
        pageid = request.GET["page"]
    except KeyError:
        pageid = 1
    page = lst.paginator.getpage(pageid)
    if page:
        content = lst.fetch(page.id_start, page.id_stop).render(request)
        navbar = lst.render_navbar(page)
    else:
        content = "Empty folder"
        navbar = ""
    ctx = {"status" : "ok", "listing" : content, "navbar" : navbar}
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

def fetchmail(request, mail_id, all=False):
    mbc = IMAPconnector(parameters.get("webmail", "SERVER_ADDRESS"), 143)
    mbc.login(request.user.username, request.session["password"])
    res = mbc.fetch(start=mail_id, all=all)
    if len(res):
        return res[0]
    return None

@login_required
def viewmail(request, mail_id):
    header = fetchmail(request, mail_id)
    pageid = request.GET.has_key("page") and request.GET["page"] or "1"
    if header:
        return _render(request, "webmail/viewmail.html", {
                "header" : header, "pageid" : pageid
                })

@login_required
def getmailcontent(request, mail_id):
    from mailng.lib.email_listing import Email

    msg = fetchmail(request, mail_id, True)
    email = Email(msg)
    return email.render(request)
