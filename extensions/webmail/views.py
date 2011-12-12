# -*- coding: utf-8 -*-
import time
import sys
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from modoboa.admin.models import Mailbox
from modoboa.lib import parameters
from modoboa.lib.webutils import _render, _render_error, \
    getctx, _render_to_string, ajax_response, ajax_simple_response
from modoboa.lib.emailutils import split_mailbox
from modoboa.lib.email_listing import parse_search_parameters, Paginator
from modoboa.admin.lib import is_not_localadmin
from modoboa.auth.lib import *
from lib import *
from forms import *
from templatetags import webextras

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

def fetchmail(request, mbox, mailid, all=False):
    imapc = get_imapconnector(request)
    res = imapc.fetchmail(mbox, mailid)

    return res
    # res = IMAPconnector(user=request.user.username, 
    #                     password=request.session["password"]).fetch(start=mail_id, 
    #                                                                 folder=folder, 
    #                                                                 all=all)
    # if len(res):
    #     return res[0]
    # return None

# @login_required
# @is_not_localadmin()
# def viewmail(request, folder, mail_id=None):
#     from templatetags.webextras import viewm_menu

#     if request.GET.has_key("links"):
#         links = int(request.GET["links"])
#     else:
#         links = parameters.get_user(request.user, "ENABLE_LINKS") == "yes" and 1 or 0
#     url = reverse(getmailcontent, args=[folder, mail_id]) + ("?links=%d" % links)
#     content = Template("""
# <iframe width="100%" frameBorder="0" src="{{ url }}" id="mailcontent"></iframe>
# """).render(Context({"url" : url}))
#     menu = viewm_menu("", get_current_url(request), folder, mail_id,
#                       request.user.get_all_permissions())
#     mbc = IMAPconnector(user=request.user.username, 
#                         password=request.session["password"])
#     ctx = getctx("ok", **__render_common_components(request, folder, 
#                                                     menu=menu, content=content))
#     return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
@is_not_localadmin()
def getmailcontent(request):
    mbox = request.GET.get("mbox", None)
    mailid = request.GET.get("mailid", None)
    if mbox is None or mailid is None:
        raise WebmailError(_("Invalid request"))

    content = fetchmail(request, mbox, mailid, True)

    # if "class" in msg.keys() and msg["class"] == "unseen":
    #     IMAPconnector(user=request.user.username,
    #                   password=request.session["password"]).msg_read(folder, mail_id)

    email = ImapEmail(content, request.user, links=request.GET["links"])
    return _render(request, "common/viewmail.html", {
            "headers" : email.render_headers(folder=mbox, mail_id=mailid), 
            "folder" : mbox, "imapid" : mailid, "mailbody" : email.body
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
            raise WebmailError(_("Invalid request"))
    mbc = get_imapconnector(request)
    mbc.move(request.GET["msgset"], request.session["mbox"], request.GET["to"])
    resp = listmailbox(request, request.session["mbox"])
    resp.update(status="ok")
    return ajax_simple_response(resp)

@login_required
@is_not_localadmin()
def delete(request, fdname, mail_id):
    mbc = IMAPconnector(user=request.user.username,
                        password=request.session["password"])
    mbc.move(mail_id, fdname, parameters.get_user(request.user, "TRASH_FOLDER"))
    ctx = getctx("ok", next=get_current_url(request))
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
@is_not_localadmin()
def mark(request, name):
    status = request.GET.get("status", None)
    ids = request.GET.get("ids", None)
    if status is None or ids is None:
        raise WebmailError(_("Invalid request"))
    imapc = get_imapconnector(request)
    try:
        getattr(imapc, "mark_messages_%s" % status)(name, ids)
    except AttributeError:
        raise WebmailError(_("Unknown action"))

    return ajax_simple_response(
        dict(status="ok", action=status, mbox=name,
             unseen=imapc.unseen_messages(name))
        )

@login_required
@is_not_localadmin()
def empty(request, name):
    if name == parameters.get_user(request.user, "TRASH_FOLDER"):
        get_imapconnector(request).empty(name)
    return ajax_simple_response(dict(status="ok"))

@login_required
@is_not_localadmin()
def compact(request, name):
    imapc = get_imapconnector(request)
    imapc.compact(name)
    return ajax_simple_response(dict(status="ok"))

# def render_compose(request, form, posturl, email=None, insert_signature=False):
#     menu = compose_menu("", get_current_url(request), 
#                         request.user.get_all_permissions())
#     editor = parameters.get_user(request.user, "EDITOR")
#     if email is None:
#         body = ""
#         textheader = ""
#     else:
#         body = email.body
#         textheader = email.textheader
#     if insert_signature:
#         signature = EmailSignature(request.user)
#         body += str(signature)
#     randid = None
#     if not request.GET.has_key("id"):
#         if request.session.has_key("compose_mail"):
#             clean_attachments(request.session["compose_mail"]["attachments"])
#         randid = set_compose_session(request)
#     elif not request.session.has_key("compose_mail") \
#             or request.session["compose_mail"]["id"] != request.GET["id"]:
#         randid = set_compose_session(request)

#     attachments = request.session["compose_mail"]["attachments"]
#     if len(attachments):
#         short_att_list = "(%s)" \
#             % ", ".join(map(lambda att: att["fname"], 
#                             attachments[:2] + [{"fname" : "..."}] \
#                                 if len(attachments) > 2 else attachments))
#     else:
#         short_att_list = ""
#     content = _render_to_string(request, "webmail/compose.html", {
#             "form" : form, "bodyheader" : textheader,
#             "body" : body, "posturl" : posturl,
#             "attachments" : attachments, "short_att_list" : short_att_list
#             })
#     mbc = IMAPconnector(user=request.user.username, 
#                         password=request.session["password"])
#     ctx = getctx("ok", level=2, editor=editor, 
#                  **__render_common_components(request, request.session["folder"], 
#                                               menu=menu, content=content))
#     if randid is not None:
#         ctx["id"] = randid
#     return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

# @login_required
# @is_not_localadmin()
# def compose(request):
#     if request.method == "POST":
#         status, resp = send_mail(request, posturl=reverse(compose))
#         return resp

#     form = ComposeMailForm()
#     form.fields["from_"].initial = request.user.username
#     return render_compose(request, form, reverse(compose), insert_signature=True)

@login_required
@is_not_localadmin()
def reply(request, folder, mail_id):
    msg = fetchmail(request, folder, mail_id, True)
    if request.method == "POST":
        status, resp = send_mail(request, origmsg=msg, 
                                 posturl=reverse(reply, args=[folder, mail_id]))
        if status:
            IMAPconnector(user=request.user.username,
                          password=request.session["password"]).msg_answered(folder,
                                                                             mail_id)
        return resp

    form = ComposeMailForm()    
    email = ReplyModifier(msg, request.user, form, request.GET.has_key("all"),
                          addrfull=True, links="1")
    return render_compose(request, form, reverse(reply, args=[folder, mail_id]),
                          email)

@login_required
@is_not_localadmin()
def forward(request, folder, mail_id):
    if request.method == "POST":
        status, response = send_mail(request,
                                     posturl=reverse(forward, args=[folder, mail_id]))
        if status:
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
            return ajax_response(request, ajaxnav=True, respmsg=_("Folder created"))
            
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
            extra = {}
            if form.cleaned_data["name"] != oldname \
                    or (pf is not None and pf != oldparent):
                newname = form.cleaned_data["name"] if pf is None \
                    else "%s.%s" % (pf, form.cleaned_data["name"])
                mbc.rename_folder(request.POST["oldname"], newname)
                extra["url"] = newname
            return ajax_response(request, ajaxnav=True, 
                                 respmsg=_("Folder modified"), **extra)

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
    return ajax_response(request)

@login_required
@is_not_localadmin()
def attachments(request, tplname="webmail/attachments.html"):
    if request.method == "POST":
        csuploader = AttachmentUploadHandler()
        request.upload_handlers.insert(0, csuploader)
        error = None
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                fobj = request.FILES["attachment"]
                tmpname = save_attachment(fobj)
                request.session["compose_mail"]["attachments"] \
                    += [{"fname" : str(fobj), 
                         "content-type" : fobj.content_type,
                         "size" : fobj.size,
                         "tmpname" : os.path.basename(tmpname)}]
                request.session.modified = True
                return _render(request, "webmail/upload_done.html", {
                        "status" : "ok", "fname" : request.FILES["attachment"],
                        "tmpname" : os.path.basename(tmpname)
                        });
            except WebmailError, inst:
                error = _("Failed to save attachment: ") + str(inst)

        if csuploader.toobig:
            error = _("Attachment is too big (limit: %s)" \
                          % parameters.get_admin("MAX_ATTACHMENT_SIZE"))
        return _render(request, "webmail/upload_done.html", {
                "status" : "ko", "error" : error
                });
    ctx = {"form" : AttachmentForm(), 
           "attachments" : request.session["compose_mail"]["attachments"]}
    return _render(request, tplname, ctx)

@login_required
@is_not_localadmin()
def delattachment(request):
    if not request.session.has_key("compose_mail") \
            or not request.GET.has_key("name") \
            or not request.GET["name"]:
        return ajax_response(request, "ko", respmsg=_("Bad query"))

    error = None
    for att in request.session["compose_mail"]["attachments"]:
        if att["tmpname"] == request.GET["name"]:
            request.session["compose_mail"]["attachments"].remove(att)
            fullpath = os.path.join(settings.MEDIA_ROOT, "tmp", att["tmpname"])
            try:
                os.remove(fullpath)
            except OSError, e:
                error = _("Failed to remove attachment: ") + str(e)
                break
            request.session.modified = True
            return ajax_response(request)
    if error is None:
        error = _("Unknown attachment")
    return ajax_response(request, "ko", respmsg=error)

#
# NEW CODE STARTS HERE
#
def render_mboxes_list(request, imapc):
    """Return the HTML representation of a mailboxes list

    :param request: a ``Request`` object
    :param imap: an ``IMAPconnector` object
    :return: a string
    """
    curmbox = request.session.get("mbox", "INBOX")
    return _render_to_string(request, "webmail/folders.html", {
            "titlebar" : True,
            "selected" : curmbox,
            "folders" : imapc.getfolders(request.user),
            "withmenu" : True,
            "withunseen" : True
            })

def set_nav_params(request):
    if not request.session.has_key("navparams"):
        request.session["navparams"] = {}
        
    request.session["pageid"] = \
        int(request.GET.get("page", 1))
    if not request.GET.get("order", False):
        if not request.session["navparams"].has_key("order"):
            request.session["navparams"]["order"] = "-date"
    else:
        request.session["navparams"]["order"] = request.GET.get("order")

    for p in ["pattern", "criteria"]:
        if request.GET.get(p, False):
            request.session["navparams"][p] = request.GET[p]
        elif request.session["navparams"].has_key(p):
            del request.session["navparams"][p]

def listmailbox(request, defmailbox="INBOX"):
    """Mailbox content listing

    Return a list of messages contained in the specified mailbox. The
    number of elements returned depends on the ``MESSAGES_PER_PAGE``
    parameter. (user preferences)

    :param request: a ``Request`` object
    :param defmailbox: the default mailbox (when not present inside request arguments)
    :return: a dictionnary
    """
    mbox = request.GET.get("name", defmailbox)
    request.session["mbox"] = mbox
    set_nav_params(request)

    lst = ImapListing(request.user, request.session["password"],
                      baseurl="?action=listmailbox&name=%s&" % mbox,
                      folder=mbox, **request.session["navparams"])

    return lst.render(request, request.session["pageid"])

def render_compose(request, form, posturl, email=None, insert_signature=False):
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
    randid = None
    if not request.GET.has_key("id"):
        if request.session.has_key("compose_mail"):
            clean_attachments(request.session["compose_mail"]["attachments"])
        randid = set_compose_session(request)
    elif not request.session.has_key("compose_mail") \
            or request.session["compose_mail"]["id"] != request.GET["id"]:
        randid = set_compose_session(request)

    attachments = request.session["compose_mail"]["attachments"]
    if len(attachments):
        short_att_list = "(%s)" \
            % ", ".join(map(lambda att: att["fname"], 
                            attachments[:2] + [{"fname" : "..."}] \
                                if len(attachments) > 2 else attachments))
    else:
        short_att_list = ""
    content = _render_to_string(request, "webmail/compose.html", {
            "form" : form, "bodyheader" : textheader,
            "body" : body, "posturl" : posturl,
            "attachments" : attachments, "short_att_list" : short_att_list
            })

    ctx = dict(listing=content, editor=editor)
    if randid is not None:
        ctx["id"] = randid
    return ctx

def compose(request):
    form = ComposeMailForm()
    form.fields["from_"].initial = request.user.username
    return render_compose(request, form, "compose", insert_signature=True)

def viewmail(request):
    mailid = request.GET.get("mailid", None)
    if mailid is None:
        raise WebmailError(_("Invalid request"))

    links = 1
    url = reverse(getmailcontent) + "?mbox=%s&mailid=%s&links=%d" % \
        (request.session["mbox"], mailid, links)
    content = Template("""
<iframe width="100%" frameBorder="0" src="{{ url }}" id="mailcontent"></iframe>
""").render(Context({"url" : url}))

    return dict(listing=content, menuargs=dict(mail_id=mailid))

@login_required
@is_not_localadmin()
def submailboxes(request):
    topmailbox = request.GET.get('topmailbox', '')
    mboxes = get_imapconnector(request).getfolders(request.user, topmailbox)
    return ajax_simple_response(dict(status="ok", mboxes=mboxes))

@login_required
@is_not_localadmin()
def newindex(request):
    """Webmail actions handler

    Problèmes liés à la navigation 'anchor based'
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Lors d'un rafraichissemt complet, une première requête est envoyée
    vers /webmail/. On ne connait pas encore l'action qui va être
    demandée mais on peut déjà envoyer des informations indépendantes
    (comme les dossiers, le quota).

    Si on se contente de cela, l'affichage donnera un aspect décomposé
    qui n'est pas très séduisant (à cause de la latence notamment). Il
    faudrait pouvoir envoyer le menu par la même occasion, le souci
    étant de savoir lequel...

    Une solution possible : il suffirait de déplacer le menu vers la
    droite pour l'aligner avec le contenu, remonter la liste des
    dossiers (même hauteur que le menu) et renvoyer le menu en même
    temps que le contenu. Le rendu sera plus uniforme je pense.

    """
    action = request.GET.get("action", None)
    json = request.GET.get("json", False)

    if action is not None:
        try:
            response = globals()[action](request)
        except KeyError:
            raise WebmailError(_("Undefined action"))
    else:
        if json:
            raise WebmailError(_("Bad request"))
        response = dict(deflocation="?action=listmailbox", 
                        defcallback="wm_updatelisting")

    curmbox = request.session.get("mbox", "INBOX")
    if not json:
        request.session["lastaction"] = None
        imapc = get_imapconnector(request)
        response["refreshrate"] = \
            int(parameters.get_user(request.user, "REFRESH_INTERVAL")) * 1000
        response["mboxes"] = render_mboxes_list(request, imapc)
        return _render(request, "webmail/index.html", response)

    if request.session["lastaction"] != action:
        extra_args = {}
        if response.has_key("menuargs"):
            extra_args = response["menuargs"]
            del response["menuargs"]
        try:
            response["menu"] = \
                getattr(webextras, "%s_menu" % action)("", curmbox, request.user, **extra_args)
        except KeyError:
            pass

    response.update(status="ok", callback=action)
    return ajax_simple_response(response)
