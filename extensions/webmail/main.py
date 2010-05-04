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
from mailng.lib import events, parameters, _render, _render_error, getctx
from imap_listing import *
from forms import *
from templatetags.webextras import *
from lib.email_listing import parse_search_parameters

def init():
    events.register("UserMenuDisplay", menu)
    events.register("UserLogin", userlogin)
    parameters.register("webmail", "IMAP_SERVER", "string", "127.0.0.1",
                        help=_("Address of your IMAP server"))
    parameters.register("webmail", "IMAP_SECURED", "list_yesno", "no",
                        help=_("Use a secured connection to access IMAP server"))
    parameters.register("webmail", "IMAP_PORT", "int", "143",
                        help=_("Listening port of your IMAP server"))
    parameters.register("webmail", "SMTP_SERVER", "string", "127.0.0.1",
                        help=_("Address of your SMTP server"))
    parameters.register("webmail", "SMTP_PORT", "int", "25",
                        help=_("Listening port of your SMTP server"))
    parameters.register("webmail", "SMTP_AUTHENTICATION", "list_yesno", "no",
                        help=_("Server needs authentication"))
    parameters.register("webmail", "SMTP_SECURED", "list_yesno", "no",
                        help=_("Use a secured connection to access SMTP server"))

def destroy():
    events.unregister("UserMenuDisplay", menu)
    events.unregister("UserLogin", userlogin)
    parameters.unregister_app("webmail")

def infos():
    return {
        "name" : "Webmail",
        "version" : "1.0",
        "description" : _("Simple IMAP webmail")
        }

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

def __get_current_url(request):
    res = "%s?page=%s" % (request.session["folder"], request.session["page"])
    for p in ["criteria", "pattern", "order"]:
        if p in request.session.keys():
            res += "&%s=%s" % (p, request.session[p])
    return res

def userlogin(**kwargs):
    kwargs["request"].session["password"] = kwargs["password"]

@login_required
def folder(request, name, updatenav=True):
    if not name:
        name = "INBOX"
    order = request.GET.has_key("order") and request.GET["order"] or "-date"
    if updatenav:
        pageid = request.GET.has_key("page") and int(request.GET["page"]) or 1
        if not "navparams" in request.session.keys():
            request.session["navparams"] = {}
        request.session["folder"] = name
        request.session["page"] = pageid
        if order:
            request.session["navparams"]["order"] = order
        parse_search_parameters(request)
    else:
        # Internal usage
        order = request.session["navparams"]["order"]

    optparams = {}
    if request.session.has_key("pattern"):
        optparams["pattern"] = request.session["pattern"]
        optparams["criteria"] = request.session["criteria"]
    else:
        optparams["reset"] = True
    lst = ImapListing(request.user.username, request.session["password"],
                      baseurl=name, folder=name, order=order, **optparams)

    page = lst.paginator.getpage(request.session["page"])
    if page:
        content = lst.fetch(request, page.id_start, page.id_stop)
        navbar = lst.render_navbar(page)
    else:
        content = "Empty folder"
        navbar = ""
    folders = render_to_string("webmail/folders.html", {
            "folders" : lst.getfolders()
            })
    ctx = getctx("ok", folders=folders, listing=content, navbar=navbar,
                 menu=listing_menu("", name, request.user.get_all_permissions()))
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
def index(request):
    try:
        navp = request.session.has_key("navparams") \
            and request.session["navparams"] or {}
        lst = ImapListing(request.user.username, request.session["password"],
                          baseurl="INBOX", navparams=navp, folder="INBOX",
                          empty=True)
    except Exception, exp:
        return _render_error(request, {"error" : exp})
    return lst.render(request)

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
    menu = viewm_menu("", __get_current_url(request), folder, mail_id,
                      request.user.get_all_permissions())
    ctx = getctx("ok", menu=menu, listing=content)
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
def getmailcontent(request, folder, mail_id):
    msg = fetchmail(request, folder, mail_id, True)
    if "class" in msg.keys() and msg["class"] == "unseen":
        IMAPconnector(request).msg_read(folder, mail_id)
        email = ImapEmail(msg, mode="html", links="1")
    try:
        pageid = request.session["page"]
    except KeyError:
        pageid = "1"
    return _render(request, "common/viewmail.html", {
            "headers" : email.render_headers(folder, mail_id), 
            "folder" : folder, "imapid" : mail_id, "mailbody" : email.body, 
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
    mbc = IMAPconnector(request)
    mbc.move(request.GET["msgset"], request.session["folder"], request.GET["to"])
    return folder(request, request.session["folder"], False)

@login_required
def delete(request, fdname, mail_id):
    mbc = IMAPconnector(request)
    mbc.move(mail_id, fdname, "Trash")
    return folder(request, fdname, False)

@login_required
def mark(request, name):
    if not request.GET.has_key("status") or not request.GET.has_key("ids"):
        return
    mbc = IMAPconnector(request)
    try:
        getattr(mbc, "msg_%s" % request.GET["status"])(name, request.GET["ids"])
    except AttributeError:
        pass
    return folder(request, name, False)

@login_required
def empty(request, name):
    if name == "Trash":
        mbc = IMAPconnector(request)
        mbc.empty(name)
    return folder(request, name, False)

@login_required
def compact(request, name):
    mbc = IMAPconnector(request)
    mbc.compact(name)
    return folder(request, name, False)

def render_compose(request, form, posturl, bodyheader=None, body=None):
    menu = compose_menu("", __get_current_url(request), 
                        request.user.get_all_permissions())
    content = render_to_string("webmail/compose.html", {
            "form" : form, "bodyheader" : bodyheader, "body" : body,
            "posturl" : posturl
            })
    ctx = getctx("ok", level=2, menu=menu, listing=content)
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

def send_mail(request, withctx=False, origmsg=None):
    form = ComposeMailForm(request.POST)
    if form.is_valid():
        from email.mime.text import MIMEText
        from email.utils import make_msgid, formatdate
        import smtplib

        msg = MIMEText(request.POST["id_body"].encode("utf-8"), 
                       _charset="utf-8")
        msg["Subject"] = request.POST["subject"]
        msg["From"] = request.POST["from_"]
        msg["To"] = request.POST["to"]
        msg["Message-ID"] = make_msgid()
        msg["User-Agent"] = "MailNG"
        msg["Date"] = formatdate(time.time(), True)
        if origmsg and origmsg.has_key("Message-ID"):
            msg["References"] = msg["In-Reply-To"] = origmsg["Message-ID"]
        rcpts = msg['To'].split(',')
        if "cc" in request.POST.keys():
            msg["Cc"] = request.POST["cc"]
            rcpts += msg["Cc"].split(",")
        try:
            s = smtplib.SMTP(parameters.get("webmail", "SMTP_SERVER"))
            if parameters.get("webmail", "SMTP_SECURED") == "yes":
                s.starttls()
        except (smtplib.SMTPException, ssl.SSLError), error:
            print error
            # Prévoir la remontée de cette erreur au niveau du client!!

        if parameters.get("webmail", "SMTP_AUTHENTICATION") == "yes":
            s.login(request.user.username, request.session["password"])
        s.sendmail(msg['From'], rcpts, msg.as_string())
        s.quit()
        IMAPconnector(request).push_mail("Sent", msg)
        ctx = getctx("ok", url=__get_current_url(request))
    else:
        ctx = getctx("ko", level=2, listing=render_to_string("webmail/compose.html", 
                                                    {"form" : form}))
    if not withctx:
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
    return ctx, HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
def compose(request):
    if request.method == "POST":
        return send_mail(request)

    form = ComposeMailForm()
    form.fields["from_"].initial = request.user.username
    return render_compose(request, form, reverse(compose))

@login_required
def reply(request, folder, mail_id):
    msg = fetchmail(request, folder, mail_id, True)
    if request.method == "POST":
        ctx, r = send_mail(request, True, origmsg=msg)
        if ctx["status"] == "ok":
            IMAPconnector(request).msg_answered(folder, mail_id)
        return r
    email = ImapEmail(msg, True)
    lines = email.body.split('\n')
    body = ""
    for l in lines:
        if body != "":
            body += "\n"
        body += ">%s" % l
    form = ComposeMailForm()
    form.fields["from_"].initial = request.user.username
    if not "Reply-To" in msg.keys():
        form.fields["to"].initial = email.From
    else:
        form.fields["to"].initial = email.Reply_To
    if request.GET.has_key("all"):
        form.fields["cc"].initial = ""
        toparse = msg["To"].split(",")
        if "Cc" in msg.keys():
            toparse += msg["Cc"].split(",")
        for addr in toparse:
            tmp = EmailAddress(addr)
            if tmp.address and tmp.address == request.user.username:
                continue
            if form.fields["cc"].initial != "":
                form.fields["cc"].initial += ", "
            form.fields["cc"].initial += tmp.fulladdress
    m = re.match("re\s*:\s*.+", email.Subject.lower())
    if m:
        form.fields["subject"].initial = email.Subject
    else:
        form.fields["subject"].initial = "Re: %s" % email.Subject
    textheader = "%s %s" % (email.From, _("wrote:"))
    return render_compose(request, form, reverse(reply, args=[folder, mail_id]),
                          textheader, body)

@login_required
def forward(request, folder, mail_id):
    if request.method == "POST":
        ctx, response = send_mail(request, True)
        if ctx["status"] == "ok":
            IMAPconnector(request).msgforwarded(folder, mail_id)
        return response

    msg = fetchmail(request, folder, mail_id, True)
    email = ImapEmail(msg, True)
    textheader = "----- %s -----" % _("Original message")
    textheader += "\n%s: %s" % (_("Subject"), email.Subject)
    textheader += "\n%s: %s" % (_("Date"), msg["Date"])
    for hdr in ["From", "To", "Reply-To"]:
        try:
            key = re.sub("-", "_", hdr)
            value = getattr(email, key)
            textheader += "\n%s: %s" % (_(hdr), value)
        except:
            pass
    textheader += "\n"

    form = ComposeMailForm()
    form.fields["from_"].initial = request.user.username
    form.fields["subject"].initial = "Fwd: %s" % email.Subject
    return render_compose(request, form, reverse(forward, args=[folder, mail_id]), 
                          textheader, email.body)
