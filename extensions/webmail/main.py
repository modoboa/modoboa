# -*- coding: utf-8 -*-
import time
import sys
from django.http import HttpResponse, Http404
from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.conf.urls.defaults import include
from django.contrib.auth.decorators import login_required
from mailng.admin.models import Mailbox
from mailng.lib import events, parameters, _render, _render_error
from imap_listing import *
from forms import *
from templatetags.webextras import *
from imap_listing import ImapEmail

def init():
    events.register("UserMenuDisplay", menu)
    events.register("UserLogin", userlogin)
    parameters.register("webmail", "IMAP_SERVER", "string", "127.0.0.1",
                        help=_("Address of your IMAP server"))
    parameters.register("webmail", "IMAP_SECURED", "list_yesno", "no",
                        help=_("Use a secure connexion to access IMAP server"))
    parameters.register("webmail", "IMAP_PORT", "int", "143",
                        help=_("Listening port of your IMAP server"))
    parameters.register("webmail", "SMTP_SERVER", "string", "127.0.0.1",
                        help=_("Address of your SMTP server"))
    parameters.register("webmail", "SMTP_PORT", "int", "25",
                        help=_("Listening port of your SMTP server"))

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

def userlogin(**kwargs):
    kwargs["request"].session["password"] = kwargs["password"]

def getctx(status, level=1, **kwargs):
    callername = sys._getframe(level).f_code.co_name
    ctx = {"status" : status, "callback" : callername}
    for kw, v in kwargs.iteritems():
        ctx[kw] = v
    return ctx

@login_required
def folder(request, name, updatenav=True):
    if not name:
        name = "INBOX"
    order = request.GET.has_key("order") and request.GET["order"] or None
    if updatenav:
        pageid = request.GET.has_key("page") and int(request.GET["page"]) or 1
        if not "navparams" in request.session.keys():
            request.session["navparams"] = {}
        request.session["folder"] = name
        request.session["page"] = pageid
        if order:
            request.session["navparams"]["order"] = order
    else:
        # Internal usage
        order = request.session["navparams"]["order"]

    lst = ImapListing(request.user.username, request.session["password"],
                      name, folder=name, order=order)
    page = lst.paginator.getpage(request.session["page"])
    if page:
        content = lst.fetch(request, page.id_start, page.id_stop)
        navbar = lst.render_navbar(page)
    else:
        content = "Empty folder"
        navbar = ""
    ctx = getctx("ok", listing=content, navbar=navbar,
                 menu=listing_menu("", name, request.user.get_all_permissions()))
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
def index(request):
    try:
        navp = request.session.has_key("navparams") \
            and request.session["navparams"] or {}
        lst = ImapListing(request.user.username, request.session["password"],
                          "INBOX", navparams=navp, folder="INBOX")
    except Exception as exp:
        return _render_error(request, {"error" : exp})
    return lst.render(request, empty=True)

def fetchmail(request, folder, mail_id, all=False):
    res = IMAPconnector(request).fetch(start=mail_id, folder=folder, all=all)
    if len(res):
        return res[0]
    return None

@login_required
def viewmail(request, folder, mail_id=None):
    from templatetags.webextras import viewm_menu

    content = Template("""
<iframe width="100%" frameBorder="0" src="{{ url }}" id="mailcontent"></iframe>
""").render(Context({"url" : reverse(getmailcontent, args=[folder, mail_id])}))
    menu = viewm_menu("", request.session, mail_id,
                      request.user.get_all_permissions())
    ctx = getctx("ok", menu=menu, listing=content)
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
def getmailcontent(request, folder, mail_id):
    msg = fetchmail(request, folder, mail_id, True)
    if "class" in msg.keys() and msg["class"] == "unseen":
        IMAPconnector(request).msgseen(msg["imapid"])
        email = ImapEmail(msg, mode="html", links="1")
    try:
        pageid = request.session["page"]
    except KeyError:
        pageid = "1"
    folder, imapid = msg["imapid"].split("/")
    return _render(request, "webmail/viewmail.html", {
            "headers" : email.render_headers(folder, mail_id), 
            "folder" : folder, "imapid" : imapid, "mailbody" : email.body, 
            "pre" : email.pre
            })

@login_required
def getattachment(request, folder, mail_id):
    msg = fetchmail(request, folder, mail_id, True)
    for part in msg.walk():
        fname = part.get_filename()
        if fname is None:
            continue
        decoded = decode_header(fname)
        if decoded[0][1] is None:
            fname = unicode(decoded[0][0])
        else:
            fname = unicode(decoded[0][0], decoded[0][1])
        if fname == request.GET["fname"]:
            resp = HttpResponse(part.get_payload(decode=1))
            for hdr in ["Content-Disposition", "Content-Type"]:
                resp[hdr] = re.sub("\s", "", part[hdr])
            resp["Content-Length"] = len(resp.content)
            return resp
    raise Http404

@login_required
def move(request):
    for arg in ["msgset", "to"]:
        if not request.GET.has_key(arg):
            return
    msgset = []
    fdname = ""
    for item in request.GET["msgset"].split(","):
        fdname, id = item.split("/")
        msgset += [id]
    mbc = IMAPconnector(request)
    mbc.move(",".join(msgset), fdname, request.GET["to"])
    return folder(request, fdname, False)

@login_required
def delete(request, fdname, mail_id):
    mbc = IMAPconnector(request)
    mbc.move(mail_id, fdname, "Trash")
    return folder(request, fdname, False)

@login_required
def empty(request, name):
    mbc = IMAPconnector(request)
    mbc.empty(name)
    return folder(request, name, False)

def render_compose(request, form, bodyheader=None, body=None):
    menu = compose_menu("", request.session, request.user.get_all_permissions())
    content = render_to_string("webmail/compose.html", {
            "form" : form, "bodyheader" : bodyheader, "body" : body
            })
    ctx = getctx("ok", level=2, menu=menu, listing=content)
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
def compose(request):
    if request.method == "POST":
        form = ComposeMailForm(request.POST)
        if form.is_valid():
            from email.mime.text import MIMEText
            import smtplib

            msg = MIMEText(request.POST["id_body"].encode("utf-8"), 
                           _charset="utf-8")
            msg["Subject"] = request.POST["subject"]
            msg["From"] = request.POST["from_"]
            msg["to"] = request.POST["to"]
            s = smtplib.SMTP(parameters.get("webmail", "SMTP_SERVER"))
            s.sendmail(msg['From'], [msg['To']], msg.as_string())
            s.quit()
            return folder(request, request.session["navparams"]["folder"], False)

    form = ComposeMailForm()
    form.fields["from_"].initial = request.user.username
    return render_compose(request, form)

@login_required
def reply(request, folder, mail_id):
    if request.method == "POST":
        return
    msg = fetchmail(request, folder, mail_id, True)
    email = ImapEmail(msg)
    lines = email.body.split('\n')
    body = ""
    for l in lines:
        if body != "":
            body += "\n"
        body += ">%s" % l
    form = ComposeMailForm()
    form.fields["from_"].initial = request.user.username
    form.fields["to"].initial = msg["From"]
    m = re.match("re\s*:\s*.+", msg["Subject"].lower())
    if m:
        form.fields["subject"].initial = msg["Subject"]
    else:
        form.fields["subject"].initial = "Re: %s" % msg["Subject"]
    textheader = msg["From"] + " " + _("wrote:")
    return render_compose(request, form, textheader, body)
