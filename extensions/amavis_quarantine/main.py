# -*- coding: utf-8 -*-

"""
"""
from django.shortcuts import get_object_or_404, render_to_response
from django.conf.urls.defaults import *
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from mailng.lib import events
from mailng.lib import _render, _ctx_ok, _ctx_ko
from mailng.lib import db
from mailng.admin.models import Mailbox

def init():
    events.register("UserMenuDisplay", menu)

def urls():
    return (r'^mailng/quarantine/', 
            include('mailng.extensions.amavis_quarantine.urls'))

def menu(**kwargs):
    return [
        {"name" : _("Quarantine"),
         "url" : reverse(index),
         "img" : "/static/pics/quarantine.png"}
        ]

def index(request):
    if not request.user.is_superuser:
        mb = Mailbox.objects.get(user=request.user.id)
        filter = "AND maddr.email='%s'" % mb.full_address
    else:
        filter = ""
    cursor = db.getconnection("amavis_quarantine").cursor()
    cursor.execute("""
SELECT msgs.from_addr, maddr.email, msgs.subject, msgs.content, quarantine.mail_id
FROM quarantine, maddr, msgrcpt, msgs
WHERE quarantine.mail_id=msgrcpt.mail_id
AND msgrcpt.rid=maddr.id
AND msgrcpt.mail_id=msgs.mail_id
AND quarantine.chunk_ind=1
%s
""" % filter)
    emails = []
    rows = cursor.fetchall()
    for row in rows:
        emails.append({"from" : row[0], "to" : row[1], 
                       "subject" : row[2], "content" : row[3],
                       "mailid" : row[4]})
    
#     cursor.execute("SELECT count(*) AS cnt FROM quarantine")
#     row = cursor.fetchone()
#     cnt = row[0]
        
    paginator = Paginator(emails, 10)
    try:
        pagenum = int(request.GET.get('page', '1'))
    except ValueError:
        pagenum = 1
    page = paginator.page(pagenum)
    return _render(request, 'amavis_quarantine/index.html', {
            "count" : len(rows), "emails" : page
            })
