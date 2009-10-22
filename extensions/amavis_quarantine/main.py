# -*- coding: utf-8 -*-

"""
"""
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template.loader import render_to_string
from django.template import Template
from django.utils import simplejson
from django.conf.urls.defaults import *
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.contrib.auth.decorators \
    import login_required
from mailng.lib import events
from mailng.lib import _render, _ctx_ok, _ctx_ko, decode
from mailng.lib import db
from mailng.admin.models import Mailbox
from datetime import datetime
import email
import re
import os
import lxml.html
from lxml.html.clean import Cleaner

attached_map = {}

def map_cid(url):
    map = globals()["attached_map"]
    m = re.match(".*cid:([^\"]+)", url)
    if m:
        if map.has_key(m.group(1)):
            return map[m.group(1)]
    return url
    
def init():
    events.register("UserMenuDisplay", menu)

def urls():
    return (r'^mailng/quarantine/', 
            include('mailng.extensions.amavis_quarantine.urls'))

def menu(**kwargs):
    if kwargs["target"] != "user_menu_box":
        return []
    return [
        {"name" : _("Quarantine"),
         "url" : reverse(index),
         "img" : "/static/pics/quarantine.png"}
        ]

def lookup(*args):
    filter = ""
    for a in args:
        if not a:
            continue
        if a[0] == "&":
            filter += " AND "
        else:
            filter += " OR "
        filter += a[1:]
    conn = db.getconnection("amavis_quarantine")
    status, cursor = db.execute(conn, """
SELECT msgs.from_addr, maddr.email, msgs.subject, msgs.content, quarantine.mail_id,
       msgs.time_num, msgs.content
FROM quarantine, maddr, msgrcpt, msgs
WHERE quarantine.mail_id=msgrcpt.mail_id
AND msgrcpt.rid=maddr.id
AND msgrcpt.mail_id=msgs.mail_id
AND quarantine.chunk_ind=1
%s
ORDER BY msgs.time_num DESC
""" % filter)  
    return cursor

def render_listing(request, cursor):
    emails = []
    rows = cursor.fetchall()
    for row in rows:
        emails.append({"from" : row[0], "to" : row[1], 
                       "subject" : row[2], "content" : row[3],
                       "mailid" : row[4], "time" : datetime.fromtimestamp(row[5]),
                       "type" : row[6]})
    
    paginator = Paginator(emails, 10)
    try:
        pagenum = int(request.GET.get('page', '1'))
    except ValueError:
        pagenum = 1
    page = paginator.page(pagenum)
    return render_to_string("amavis_quarantine/listing.html", {
            "count" : len(rows), 
            "emails" : page, "current_page" : pagenum, 
            "last_page" : paginator._get_num_pages()
            })

@login_required
def index(request, message=None):
    if not request.user.is_superuser:
        mb = Mailbox.objects.get(user=request.user.id)
        filter = "&maddr.email='%s'" % mb.full_address
    else:
        filter = None
    cursor = lookup(filter)

    return _render(request, 'amavis_quarantine/index.html', {
            "content" : render_listing(request, cursor)
            })

@login_required
def viewmail_plain(request, content):
    body = decode(content)
    return (True, body)

@login_required
def viewmail_html(request, content):
    links = request.GET.has_key("links") and request.GET["links"] or "0"
    html = lxml.html.fromstring(content) 
    if links == "0":
        html.rewrite_links(lambda x: None)
    else:
        html.rewrite_links(map_cid)
    body = lxml.html.tostring(html)
    body = Template(decode(body)).render({})
    return (False, body)

@login_required
def getmailcontent(request, mail_id):
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
    contents = {"html" : "", "plain" : ""}
    for part in msg.walk():
        print part.get_content_type()
        if part.get_content_maintype() == 'multipart':
            continue
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
                    attached_map[m.group(1)] = path
                else:
                    attached_map[part["Content-ID"]] = path

    if not contents.has_key(mode) or contents[mode] == "":
        if mode == "html":
            mode = "plain"
        else:
            mode = "html"
    (pre, body) = globals()["viewmail_%s" % mode](request, contents[mode])
    return _render(request, 'amavis_quarantine/getmailcontent.html', {
            "body" : body, "pre" : pre
            })
    
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
    if count == 1:
        mail_id = "'%s'" % mail_id
    status, error = db.execute(conn, 
                               "DELETE FROM msgs WHERE mail_id IN (%s)" % mail_id)
    if status:
        message = _("%d message%s deleted successfully" \
                        % (count, count > 1 and "s" or ""))
    else:
        message = error
    return _redirect_to_index(request, message, count)

@login_required
def release(request, mail_id, count=1):
    conn = db.getconnection("amavis_quarantine")
    if count == 1:
        mail_id = "'%s'" % mail_id
    status, cursor = db.execute(conn, """
SELECT msgs.mail_id,secret_id,quar_type,maddr.email FROM msgs, maddr, msgrcpt
WHERE msgrcpt.mail_id=msgs.mail_id AND msgrcpt.rid=maddr.id AND msgs.mail_id IN (%s)
""" % (mail_id))
    emails = {}
    for row in cursor.fetchall():
        if not emails.has_key(row[0]):
            emails[row[0]] = {}
            emails[row[0]]["rcpts"] = []
        emails[row[0]]["secret"] = row[1]
        emails[row[0]]["rcpts"] += [row[3]]
    count = 0
    error = None
    for k, values in emails.iteritems():
        cmd = "/tmp/amavisd-release "
        cmd += "%s %s" % (k, values["secret"])
        for rcpt in values["rcpts"]:
            cmd += " %s" % rcpt
        cmd += "\n"
        result = os.system(cmd)
#            if re.search("250 [^\s]+ Ok", result):
        if not result:
            count += 1
        else:
            error = result
            break
    if not error:
        message = _("%d message%s released successfully" \
                        % (count, count > 1 and "s" or ""))
    else:
        message = error
    _redirect_to_index(request, message, count)

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
    if request.POST.has_key("release"):
        release(request, ids, count)
            
    if request.POST.has_key("delete"):
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
    cursor = lookup(filter)
    ctx = {"status" : "ok", "content" : render_listing(request, cursor)}
    return HttpResponse(simplejson.dumps(ctx),
                        mimetype="application/json")
