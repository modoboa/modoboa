# -*- coding: utf-8 -*-

"""
"""
from datetime import datetime
import time
import email
import re
import os
from django.http import HttpResponseRedirect, HttpResponse
from django.template import Template, Context
from django.utils import simplejson
from django.conf.urls.defaults import *
from django.utils.translation import ugettext as _, ungettext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators \
    import login_required
from mailng.lib import events, parameters
from mailng.lib import _render, _ctx_ok, _ctx_ko, decode, getctx
from mailng.lib import db
from mailng.admin.models import Mailbox
from lib import AMrelease
from templatetags.amextras import *
from sql_listing import *

def init():
    events.register("UserMenuDisplay", menu)
    parameters.register("amavis_quarantine", "MAX_MESSAGES_AGE", "int", 14,
                        help=_("Quarantine messages maximum age (in days) before deletion"))

def urls():
    return (r'^mailng/quarantine/', 
            include('mailng.extensions.amavis_quarantine.urls'))

def menu(**kwargs):
    if kwargs["target"] == "user_menu_box":
        return [
            {"name" : _("Quarantine"),
             "url" : reverse(index),
             "img" : "/static/pics/quarantine.png"}
            ]
    return []

@login_required
def _listing(request, internal=False, filter=None):
    #start = time.time()
    if not request.user.is_superuser:
        mb = Mailbox.objects.get(user=request.user.id)
        if filter is None:
            filter = ["&maddr.email='%s'" % mb.full_address]
        else:
            filter += ["&maddr.email='%s'" % mb.full_address]
    pageid = request.GET.has_key("page") and int(request.GET["page"]) or 1
    request.session["page"] = pageid # ?? nécessaire
    lst = SQLlisting(filter, baseurl="listing/", empty=internal)
    if internal:
        return lst.render(request, pageid=int(pageid))
    page = lst.paginator.getpage(pageid)
    if page:
        content = lst.fetch(request, page.id_start, page.id_stop)
        navbar = lst.render_navbar(page)
    else:
        content = _("Empty quarantine")
        navbar = ""
    ctx = getctx("ok", listing=content, navbar=navbar,
                 menu=quar_menu("", request.user.get_all_permissions()))
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
def index(request, message=None):
    return _listing(request, True)

# @login_required
# def getmailcontent(request, mail_id):
#     from mailng.lib.email_listing import Email

#     conn = db.getconnection("amavis_quarantine")
#     status, cursor = db.execute(conn, """
# SELECT mail_text
# FROM quarantine
# WHERE quarantine.mail_id='%s'
# """ % mail_id)
#     content = ""
#     for part in cursor.fetchall():
#         content += part[0]
#     msg = email.message_from_string(content)
#     links = request.GET.has_key("links") and request.GET["links"] or "0"
#     mode = request.GET.has_key("mode") and request.GET["mode"] or "plain"
#     mail = Email(msg, mode, links)
#     return mail.render(request)
    
# @login_required
# def viewmail(request, mail_id):
#     conn = db.getconnection("amavis_quarantine")
#     status, cursor = db.execute(conn, """
# SELECT mail_text
# FROM quarantine
# WHERE quarantine.mail_id='%s'
# """ % mail_id)
#     content = ""
#     for part in cursor.fetchall():
#         content += part[0]
#     msg = email.message_from_string(content)
#     ctx = getctx("ok", )
#     return _render(request, 'amavis_quarantine/viewmail.html', {
#             "headers" : msg, "alert" : msg.get("X-Amavis-Alert"),
#             "mail_id" : mail_id, "page_id" : request.session["page"],
#             "params" : request.GET
#             })

@login_required
def getmailcontent(request, mail_id):
    from mailng.lib.email_listing import Email

    conn = db.getconnection("amavis_quarantine")
    status, cursor = db.execute(conn, """
SELECT mail_text
FROM quarantine
WHERE quarantine.mail_id='%s'
""" % mail_id)
    content = ""
    for part in cursor.fetchall():
        content += part[0]
    msg = email.message_from_string(content)
    links = request.GET.has_key("links") and request.GET["links"] or "0"
    mode = request.GET.has_key("mode") and request.GET["mode"] or "plain"
    mail = Email(msg, mode, links)
    return _render(request, "common/viewmail.html", {
            "headers" : "", 
            "mailbody" : mail.body, 
            "pre" : mail.pre
            })

@login_required
def viewmail(request, mail_id):
    args = ""
    for kw in ["mode", "links"]:
        if kw in request.GET.keys():
            args += args != "" and "&" or "?"
            args += "%s=%s" % (kw, request.GET[kw])
    content = Template("""
<iframe width="100%" frameBorder="0" src="{{ url }}" id="mailcontent"></iframe>
""").render(Context({"url" : reverse(getmailcontent, args=[mail_id]) + args}))
    menu = viewm_menu("", request.session, mail_id, request.user.get_all_permissions())
    ctx = getctx("ok", menu=menu, listing=content)
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
def viewheaders(request, mail_id):
    conn = db.getconnection("amavis_quarantine")
    status, cursor = db.execute(conn, """
SELECT mail_text
FROM quarantine
WHERE quarantine.mail_id='%s'
""" % mail_id)
    content = ""
    for part in cursor.fetchall():
        content += part[0]
    msg = email.message_from_string(content)
    return _render(request, 'amavis_quarantine/viewheader.html', {
            "headers" : msg.items()
            })

def _redirect_to_index(request, message, count):
    request.user.message_set.create(message=message)
    if count > 1:
        return
    page = request.GET.has_key("page") and request.GET["page"] or "1"
    return HttpResponseRedirect(reverse(index) + "?page=%s" % page)

@login_required
def delete(request, mail_id, count=1):
    conn = db.getconnection("amavis_quarantine")
    if mail_id[0] != "'":
        mail_id = "'%s'" % mail_id
    status, error = db.execute(conn, 
                               "DELETE FROM msgs WHERE mail_id IN (%s)" % mail_id)
    if status:
        message = ungettext("%(count)d message deleted successfully",
                            "%(count)d messages deleted successfully",
                            count) % {"count" : count}
    else:
        message = error
    ctx = getctx("ok", url="?page=%s" % request.session["page"], message=message)
    return HttpResponse(simplejson.dumps(ctx), 
                        mimetype="application/json")

@login_required
def release(request, mail_id, count=1):
    conn = db.getconnection("amavis_quarantine")
    if mail_id[0] != "'":
        mail_id = "'%s'" % mail_id
    status, cursor = db.execute(conn, """
SELECT msgs.mail_id,secret_id,quar_type,maddr.email FROM msgs, maddr, msgrcpt
WHERE msgrcpt.mail_id=msgs.mail_id AND msgrcpt.rid=maddr.id AND msgs.mail_id IN (%s)
""" % (mail_id))
    emails = {}
    amr = AMrelease()
    for row in cursor.fetchall():
        if not emails.has_key(row[0]):
            emails[row[0]] = {}
            emails[row[0]]["rcpts"] = []
        emails[row[0]]["secret"] = row[1]
        emails[row[0]]["rcpts"] += [row[3]]
    count = 0
    error = None
    for k, values in emails.iteritems():
        result = amr.sendreq(k, values["secret"], *values["rcpts"])
        if result:
            count += 1
        else:
            error = result
            break
    if not error:
        message = ungettext("%(count)d message released successfully",
                            "%(count)d messages released successfully",
                            count) % {"count" : count}
    else:
        message = error
    ctx = getctx("ok", url="?page=%s" % request.session["page"], message=message)
    return HttpResponse(simplejson.dumps(ctx), 
                        mimetype="application/json")

@login_required
def process(request):
    ids = ""
    count = len(request.POST.getlist("selection"))
    for id in request.POST.getlist("selection"):
        if ids != "":
            ids += ","
        ids += "'%s'" % id
    if ids == "":
        return HttpResponseRedirect(reverse(index))

    print "Ok c pas vide"
    if request.POST["action"] == "release":
        return release(request, ids, count)
            
    if request.POST["action"] == "delete":
        return delete(request, ids, count)

@login_required
def search(request):
    if not request.GET.has_key("pattern"):
        return
    if request.GET.has_key("criteria"):
        criteria = request.GET["criteria"].split(',')
    else:
        criteria = ["from_addr"]
    filter = ""
    pattern = re.escape(request.GET["pattern"])
    for c in criteria:
        if filter != "":
            filter += " OR "
        filter += "msgs.%s LIKE '%%%s%%'" % (c, pattern)
    filter = "&(%s)" % filter 
    return _listing(request, filter=filter)

#     lst = SQLlisting([filter])

#     page = lst.paginator.getpage(1)
#     if page:
#         content = lst.fetch(page.id_start, page.id_stop).render(request)
#         navbar = lst.render_navbar(page)
#     else:
#         content = "Empty quarantine"
#         navbar = ""
#     ctx = {"status" : "ok", "listing" : content, "navbar" : navbar}
#     return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
