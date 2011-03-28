# -*- coding: utf-8 -*-
import time
import sys
from django.http import HttpResponse, Http404
from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from modoboa.admin.models import Mailbox
from modoboa.lib import parameters, _render, _render_error, \
    getctx, is_not_localadmin, _render_to_string, split_mailbox, \
    ajax_response
from modoboa.lib.email_listing import parse_search_parameters, Paginator
from lib import *
from forms import *
from templatetags.webextras import *

def __get_current_url(request):
    res = "%s?page=%s" % (request.session["folder"], request.session["page"])
    for p in ["criteria", "pattern", "order"]:
        if p in request.session.keys():
            res += "&%s=%s" % (p, request.session[p])
    return res

def __render_common_components(request, folder_name, lst=None, content=None, menu=None):
    """Render all components that are common to all pages in the webmail

    It concerns the main listing, the viewmail and the compose
    pages. Components are : main content, folders list, pagination
    bar, quota bar.

    Two modes are available : 
     * If lst is provided, do not use content,
     * If lst is not provided, do not use content, nor menu.

    :param request: a Request object
    :param folder: the current folder
    :param lst: an ImapListing object
    :param content: the HTML that will go into the 'listing' div
    :param menu: the current page menu
    """
    if lst is not None:
        paginator = lst.paginator
        mbc = lst.mbc
        menu = listing_menu("", folder_name, request.user)
    else:
        mbc = IMAPconnector(user=request.user.username, 
                            password=request.session["password"])
        paginator = Paginator(mbc.messages_count(folder=folder_name, 
                                                 order=request.session["navparams"]["order"]), 
                              int(parameters.get_user(request.user, "MESSAGES_PER_PAGE")))
                              
    page = paginator.getpage(request.session["page"])
    if page:
        navbar = EmailListing.render_navbar(page)
        if lst:
            content = lst.fetch(request, page.id_start, page.id_stop)
    else:
        navbar = ""
        if lst:
            content = "<div class='info'>%s</div>" \
                % _("This folder contains no messages")
        
    ret = {
        "folders" : _render_to_string(request, "webmail/folders.html", {
                "titlebar" : True,
                "selected" : request.session["folder"],
                "folders" : mbc.getfolders(request.user),
                "withmenu" : True,
                "withunseen" : True
                }),
        "menu" : menu,
        "listing" : content,
        "navbar" : navbar,
        "quota" : ImapListing.computequota(mbc)
        }
    
    return ret
        

@login_required
@is_not_localadmin()
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
        optparams["elems_per_page"] = \
            int(parameters.get_user(request.user, "MESSAGES_PER_PAGE"))
    lst = ImapListing(request.user, request.session["password"],
                      baseurl=name, folder=name, order=order, 
                      **optparams)
    dico = __render_common_components(request, name, lst)
    ctx = getctx("ok", **dico)
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
@is_not_localadmin()
def index(request):
    try:
        navp = request.session.has_key("navparams") \
            and request.session["navparams"] or {}
        lst = ImapListing(request.user, request.session["password"],
                          baseurl="INBOX", navparams=navp, folder="INBOX",
                          empty=True)
    except Exception, exp:
        return _render_error(request, user_context={"error" : exp})
    return lst.render(request)

def fetchmail(request, folder, mail_id, all=False):
    res = IMAPconnector(user=request.user.username, 
                        password=request.session["password"]).fetch(start=mail_id, 
                                                                    folder=folder, 
                                                                    all=all)
    if len(res):
        return res[0]
    return None

@login_required
@is_not_localadmin()
def viewmail(request, folder, mail_id=None):
    from templatetags.webextras import viewm_menu

    if request.GET.has_key("links"):
        links = int(request.GET["links"])
    else:
        links = parameters.get_user(request.user, "ENABLE_LINKS") == "yes" and 1 or 0
    url = reverse(getmailcontent, args=[folder, mail_id]) + ("?links=%d" % links)
    content = Template("""
<iframe width="100%" frameBorder="0" src="{{ url }}" id="mailcontent"></iframe>
""").render(Context({"url" : url}))
    menu = viewm_menu("", __get_current_url(request), folder, mail_id,
                      request.user.get_all_permissions())
    mbc = IMAPconnector(user=request.user.username, 
                        password=request.session["password"])
    ctx = getctx("ok", **__render_common_components(request, folder, 
                                                    menu=menu, content=content))
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
@is_not_localadmin()
def getmailcontent(request, folder, mail_id):
    msg = fetchmail(request, folder, mail_id, True)
    if "class" in msg.keys() and msg["class"] == "unseen":
        IMAPconnector(user=request.user.username,
                      password=request.session["password"]).msg_read(folder, mail_id)
        email = ImapEmail(msg, request.user, links=request.GET["links"])
    try:
        pageid = request.session["page"]
    except KeyError:
        pageid = "1"
    return _render(request, "common/viewmail.html", {
            "headers" : email.render_headers(folder=folder, mail_id=mail_id), 
            "folder" : folder, "imapid" : mail_id, "mailbody" : email.body
            })

@login_required
@is_not_localadmin()
def getattachment(request, folder, mail_id):
    if request.GET.has_key("partnumber"):
        headers = {"Content-Type" : "text/plain",
                   "Content-Transfer-Encoding" : None}
        icon = IMAPconnector(user=request.user.username, 
                             password=request.session["password"])
        part = icon.fetchpart(mail_id, folder, request.GET["partnumber"])
        if part is not None:
            if part.get_content_maintype() == "message":
                payload = part.get_payload(0)
            else:
                payload = part.get_payload(decode=True)
            resp = HttpResponse(payload)
            for hdr, default in headers.iteritems():
                if not part.has_key(hdr):
                    if default is not None:
                        resp[hdr] = default
                    else:
                        continue
                resp[hdr] = re.sub("\s", "", part[hdr])
            # I would add this part into the previous loop if I was
            # able to use functions as default values... but I'm a bit
            # lazy :p
            if part.has_key("Content-Disposition"):
                resp["Content-Disposition"] = \
                    re.sub("\s", "", part["Content-Disposition"])
            else:
                resp["Content-Disposition"] = \
                    "attachment; filename=%s" % request.GET["fname"]
            resp["Content-Length"] = len(payload)
            return resp
    raise Http404

@login_required
@is_not_localadmin()
def move(request):
    for arg in ["msgset", "to"]:
        if not request.GET.has_key(arg):
            return
    mbc = IMAPconnector(user=request.user.username, 
                        password=request.session["password"])
    mbc.move(request.GET["msgset"], request.session["folder"], request.GET["to"])
    return folder(request, request.session["folder"], False)

@login_required
@is_not_localadmin()
def delete(request, fdname, mail_id):
    mbc = IMAPconnector(user=request.user.username,
                        password=request.session["password"])
    mbc.move(mail_id, fdname, parameters.get_user(request.user, "TRASH_FOLDER"))
    ctx = getctx("ok", next=__get_current_url(request))
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
@is_not_localadmin()
def mark(request, name):
    if not request.GET.has_key("status") or not request.GET.has_key("ids"):
        return
    mbc = IMAPconnector(user=request.user.username,
                        password=request.session["password"])
    try:
        getattr(mbc, "msg_%s" % request.GET["status"])(name, request.GET["ids"])
    except AttributeError:
        pass
    return folder(request, name, False)

@login_required
@is_not_localadmin()
def empty(request, name):
    if name == parameters.get_user(request.user, "TRASH_FOLDER"):
        mbc = IMAPconnector(user=request.user.username,
                            password=request.session["password"])
        mbc.empty(name)
    return folder(request, name, False)

@login_required
@is_not_localadmin()
def compact(request, name):
    mbc = IMAPconnector(user=request.user.username,
                        password=request.session["password"])
    mbc.compact(name)
    return folder(request, name, False)

def render_compose(request, form, posturl, email=None, insert_signature=False):
    menu = compose_menu("", __get_current_url(request), 
                        request.user.get_all_permissions())
    editor = parameters.get_user(request.user, "EDITOR")
    if email is None:
        body = ""
        textheader = ""
    else:
        body = email.body
        textheader = email.textheader
    if insert_signature:
        signature = EmailSignature(request.user)
        body += str(signature)

    content = _render_to_string(request, "webmail/compose.html", {
            "form" : form, "bodyheader" : textheader,
            "body" : body, "posturl" : posturl
            })
    mbc = IMAPconnector(user=request.user.username, 
                        password=request.session["password"])
    ctx = getctx("ok", level=2, editor=editor, 
                 **__render_common_components(request, request.session["folder"], 
                                              menu=menu, content=content))
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

def __html2plaintext(content):
    """HTML to plain text translation

    :param content: some HTML content
    """
    html = lxml.html.fromstring(content)
    plaintext = ""
    for ch in html.iter():
        p = None
        if ch.text is not None:
            p = ch.text.strip('\r\t\n')
        if ch.tag == "img":
            p = ch.get("alt")
        if p is None:
            continue
        plaintext += p + "\n"
        
    return plaintext
    
def send_mail(request, withctx=False, origmsg=None, posturl=None):
    form = ComposeMailForm(request.POST)
    error = None
    ctx = None
    if form.is_valid():
        from email.mime.text import MIMEText
        from email.utils import make_msgid, formatdate
        import smtplib

        subtype = parameters.get_user(request.user, "EDITOR")
        body = request.POST["id_body"]
        charset = "utf-8"
        if subtype == "html":
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart(_subtype="related")
            submsg = MIMEMultipart(_subtype="alternative")
            textbody = __html2plaintext(body)
            submsg.attach(MIMEText(textbody.encode(charset),
                                _subtype="plain", _charset=charset))
            body, images = find_images_in_body(body)
            submsg.attach(MIMEText(body.encode(charset), _subtype=subtype, 
                                _charset=charset))
            msg.attach(submsg)
            for img in images:
                msg.attach(img)
        else:
            msg = MIMEText(body.encode(charset), _subtype=subtype)

        msg["Subject"] = request.POST["subject"]
        address, domain = split_mailbox(request.POST["from_"])
        try:
            mb = Mailbox.objects.get(address=address, domain__name=domain)
            msg["From"] = "%s <%s>" % (mb.name, request.POST["from_"])
        except Mailbox.DoesNotExist:
            msg["From"] = request.POST["from_"]
        msg["To"] = request.POST["to"]
        msg["Message-ID"] = make_msgid()
        msg["User-Agent"] = "Modoboa"
        msg["Date"] = formatdate(time.time(), True)
        if origmsg and origmsg.has_key("Message-ID"):
            msg["References"] = msg["In-Reply-To"] = origmsg["Message-ID"]
        rcpts = msg['To'].split(',')
        if "cc" in request.POST.keys():
            msg["Cc"] = request.POST["cc"]
            rcpts += msg["Cc"].split(",")
        error = None
        try:
            secmode = parameters.get_admin("SMTP_SECURED_MODE")
            if secmode == "ssl":
                s = smtplib.SMTP_SSL(parameters.get_admin("SMTP_SERVER"),
                                     int(parameters.get_admin("SMTP_PORT")))
            else:
                s = smtplib.SMTP(parameters.get_admin("SMTP_SERVER"),
                                 int(parameters.get_admin("SMTP_PORT")))
                if secmode == "starttls":
                    s.starttls()
        except Exception, text:
            error = str(text)
        if error is None:
            if parameters.get_admin("SMTP_AUTHENTICATION") == "yes":
                s.login(request.user.username, decrypt(request.session["password"]))
            s.sendmail(msg['From'], rcpts, msg.as_string())
            s.quit()
            sentfolder = parameters.get_user(request.user, "SENT_FOLDER")
            IMAPconnector(user=request.user.username,
                          password=request.session["password"]).push_mail(sentfolder, msg)
            ctx = getctx("ok", url=__get_current_url(request))

    if ctx is None:
        listing = render_to_string("webmail/compose.html", 
                                   {"form" : form, 
                                    "body" : request.POST["id_body"].strip(),
                                    "posturl" : posturl})
        ctx = getctx("ko", level=2, error=error, listing=listing)
    if not withctx:
        return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")
    return ctx, HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
@is_not_localadmin()
def compose(request):
    if request.method == "POST":
        return send_mail(request, posturl=reverse(compose))

    form = ComposeMailForm()
    form.fields["from_"].initial = request.user.username
    return render_compose(request, form, reverse(compose), insert_signature=True)

@login_required
@is_not_localadmin()
def reply(request, folder, mail_id):
    msg = fetchmail(request, folder, mail_id, True)
    if request.method == "POST":
        ctx, r = send_mail(request, True, origmsg=msg, 
                           posturl=reverse(reply, args=[folder, mail_id]))
        if ctx["status"] == "ok":
            IMAPconnector(user=request.user.username,
                          password=request.session["password"]).msg_answered(folder,
                                                                             mail_id)
        return r

    form = ComposeMailForm()    
    email = ReplyModifier(msg, request.user, form, request.GET.has_key("all"),
                          addrfull=True, links="1")
    return render_compose(request, form, reverse(reply, args=[folder, mail_id]),
                          email)

@login_required
@is_not_localadmin()
def forward(request, folder, mail_id):
    if request.method == "POST":
        ctx, response = send_mail(request, True, 
                                  posturl=reverse(forward, args=[folder, mail_id]))
        if ctx["status"] == "ok":
            IMAPconnector(user=request.user.username,
                          password=request.session["password"]).msgforwarded(folder,
                                                                             mail_id)
        return response
    
    msg = fetchmail(request, folder, mail_id, True)
    form = ComposeMailForm()
    email = ForwardModifier(msg, request.user, form, addrfull=True, links="1")
    return render_compose(request, form, reverse(forward, args=[folder, mail_id]), 
                          email)

def separate_folder(fullname, sep="."):
    """Split a folder name

    If a separator is found in fullname, this function returns the
    corresponding name and parent folder name.
    """
    if fullname.count("."):
        parts = fullname.split(sep)
        name = parts[-1]
        parent = sep.join(parts[0:len(parts) - 1])
        return name, parent
    return fullname, None

@login_required
@is_not_localadmin()
def newfolder(request, tplname="webmail/folder.html"):
    mbc = IMAPconnector(user=request.user.username, 
                        password=request.session["password"])
    ctx = {"title" : _("Create a new folder"),
           "fname" : "newfolder",
           "submit_label" : _("Create"),
           "withmenu" : False,
           "withunseen" : False}
    ctx["folders"] = mbc.getfolders(request.user)
    if request.method == "POST":
        form = FolderForm(request.POST)
        if form.is_valid():
            pf = request.POST.has_key("parent_folder") \
                and request.POST["parent_folder"] or None
            mbc.create_folder(form.cleaned_data["name"], pf)
            return ajax_response(request, ajaxnav=True)
            
        ctx["form"] = form
        ctx["selected"] = None
        return ajax_response(request, status="ko", template=tplname, **ctx)
    
    ctx["form"] = FolderForm()
    ctx["selected"] = None
    return _render(request, tplname, ctx)

@login_required
@is_not_localadmin()
def editfolder(request, tplname="webmail/folder.html"):
    mbc = IMAPconnector(user=request.user.username, 
                        password=request.session["password"])
    ctx = {"title" : _("Edit folder"),
           "fname" : "editfolder",
           "submit_label" : _("Update"),
           "withmenu" : False,
           "withunseen" : False}
    ctx["folders"] = mbc.getfolders(request.user)
    if request.method == "POST":
        form = FolderForm(request.POST)
        if form.is_valid():
            pf = request.POST.has_key("parent_folder") \
                and request.POST["parent_folder"] or None
            ctx["selected"] = pf
            oldname, oldparent = separate_folder(request.POST["oldname"])
            try:
                extra = {}
                if form.cleaned_data["name"] != oldname \
                        or (pf is not None and pf != oldparent):
                    newname = form.cleaned_data["name"] if pf is None \
                        else "%s.%s" % (pf, form.cleaned_data["name"])
                    mbc.rename_folder(request.POST["oldname"], newname)
                    extra["url"] = newname
                return ajax_response(request, ajaxnav=True, **extra)
            except Exception:
                pass
        ctx["form"] = form
        return ajax_response(request, status="ko", template=tplname, **ctx)

    if not request.GET.has_key("name") or request.GET["name"] == "":
        return
    name = request.GET["name"]
    ctx["oldname"] = name
    name, parent = separate_folder(name)
    ctx["form"] = FolderForm()
    ctx["form"].fields["name"].initial = name
    ctx["selected"] = parent
    return _render(request, tplname, ctx)

@login_required
@is_not_localadmin()
def delfolder(request):
    if not request.GET.has_key("name") or request.GET["name"] == "":
        return
    mbc = IMAPconnector(user=request.user.username, 
                        password=request.session["password"])
    mbc.delete_folder(request.GET["name"])
    return ajax_response(request, status="ko")
