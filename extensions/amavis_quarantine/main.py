# -*- coding: utf-8 -*-

"""
"""
from datetime import datetime
import time
import email
import re
import os
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import simplejson
from django.conf.urls.defaults import *
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators \
    import login_required
from mailng.lib import events, parameters
from mailng.lib import _render, _ctx_ok, _ctx_ko, decode
from mailng.lib import db
from mailng.admin.models import Mailbox
from lib import AMrelease
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
def index(request, message=None):
    start = time.time()
    if not request.user.is_superuser:
        mb = Mailbox.objects.get(user=request.user.id)
        filter = ["&maddr.email='%s'" % mb.full_address]
    else:
        filter = None
    try:
        pageid = request.GET["page"]
        if pageid == "":
            pageid = 1
    except KeyError:
        pageid = 1
    lst = SQLlisting(filter)
    return lst.render(request, pageid=int(pageid), start=start)

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
    return mail.render(request)
    
@login_required
def viewmail(request, mail_id):
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
    return _render(request, 'amavis_quarantine/viewmail.html', {
            "headers" : msg, "alert" : msg.get("X-Amavis-Alert"),
            "mail_id" : mail_id, "page_id" : request.GET["page"],
            "params" : request.GET
            })

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
        message = _("%(count)d message%(plural)s deleted successfully" \
                        % ({"count" : count, "plural" : count > 1 and "s" or ""}))
    else:
        message = error
    return _redirect_to_index(request, message, count)

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
#         cmd = "/tmp/amavisd-release "
#         cmd += "%s %s" % (k, values["secret"])
#         for rcpt in values["rcpts"]:
#             cmd += " %s" % rcpt
#         cmd += "\n"
#         result = os.system(cmd)
#            if re.search("250 [^\s]+ Ok", result):
        if result:
            count += 1
        else:
            error = result
            break
    if not error:
        message = _("%(count)d message%(plural)s released successfully" \
                        % {"count" : count, "plural" : count > 1 and "s" or ""})
    else:
        message = error
    return _redirect_to_index(request, message, count)

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
    if request.POST["action"] == "release":
        release(request, ids, count)
            
    if request.POST["action"] == "delete":
        delete(request, ids, count)

    try:
        pagenum = int(request.POST.get('pagenum', '1'))
    except ValueError:
        pagenum = 1
    ctx = _ctx_ok(reverse(index) + "?page=%s" % pagenum)
    return HttpResponse(simplejson.dumps(ctx), 
                        mimetype="application/json")

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
    lst = SQLlisting([filter])
    try:
        pageid = request.GET["page"]
        if pageid == "":
            pageid = 1
    except KeyError:
        pageid = 1
    page = lst.paginator.getpage(pageid)
    if page:
        content = lst.fetch(page.id_start, page.id_stop).render(request)
        navbar = lst.render_navbar(page)
    else:
        content = "Empty quarantine"
        navbar = ""
    ctx = {"status" : "ok", "listing" : content, "navbar" : navbar}
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
