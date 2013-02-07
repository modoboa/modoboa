# coding: utf-8
from django.conf import settings
import os
from django.http import HttpResponse
from django.template import Template, Context
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from modoboa.lib import parameters
from modoboa.lib.webutils import _render, _render_to_string, ajax_response, ajax_simple_response
from modoboa.lib.decorators import needs_mailbox
from exceptions import WebmailError
from forms import FolderForm, AttachmentForm, ComposeMailForm
from imaputils import get_imapconnector, IMAPconnector, separate_mailbox
from lib import decode_payload, AttachmentUploadHandler, save_attachment, ImapListing, EmailSignature, clean_attachments, set_compose_session, send_mail, ImapEmail
from templatetags import webextras

@login_required
@needs_mailbox()
def getattachment(request):
    """Fetch a message attachment

    FIXME: par manque de caching, le bodystructure du message est
    redemandé pour accéder aux headers de cette pièce jointe.

    :param request: a ``Request`` object
    """
    mbox = request.GET.get("mbox", None)
    mailid = request.GET.get("mailid", None)
    pnum = request.GET.get("partnumber", None)
    if not mbox or not mailid or not pnum:
        raise WebmailError(_("Invalid request"))

    headers = {"Content-Type" : "text/plain",
               "Content-Transfer-Encoding" : None}
    imapc = get_imapconnector(request)
    partdef, payload = imapc.fetchpart(mailid, mbox, pnum)
    resp = HttpResponse(decode_payload(partdef["encoding"], payload))
    resp["Content-Type"] = partdef["Content-Type"]
    resp["Content-Transfer-Encoding"] = partdef["encoding"]
    if partdef["disposition"] != 'NIL':
        disp = partdef["disposition"]
        # FIXME : ugly hack, see fetch_parser.py for more explanation
        # :p
        if type(disp[1][0]) != dict:
            cd = '%s; %s="%s"' % (disp[0], disp[1][0], disp[1][1])
        else:
            cd = '%s; %s="%s"' % (disp[0], disp[1][0]['struct'][0], disp[1][0]['struct'][1])
    else:
        cd = 'attachment; filename="%s"' % request.GET["fname"]
    resp["Content-Disposition"] = cd
    resp["Content-Length"] = partdef["size"]
    return resp

@login_required
@needs_mailbox()
def move(request):
    for arg in ["msgset", "to"]:
        if not request.GET.has_key(arg):
            raise WebmailError(_("Invalid request"))
    mbc = get_imapconnector(request)
    mbc.move(request.GET["msgset"], request.session["mbox"], request.GET["to"])
    resp = listmailbox(request, request.session["mbox"], update_session=False)
    resp.update(status="ok")
    return ajax_simple_response(resp)

@login_required
@needs_mailbox()
def delete(request):
    mbox = request.GET.get("mbox", None)
    mailid = request.GET.get("mailid", None)
    if mbox is None or mailid is None:
        raise WebmailError(_("Invalid request"))
    mbc = get_imapconnector(request)
    mbc.move(mailid, mbox, parameters.get_user(request.user, "TRASH_FOLDER"))
    resp = dict(status="ok")
    return ajax_simple_response(resp)

@login_required
@needs_mailbox()
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
@needs_mailbox()
def empty(request, name):
    if name != parameters.get_user(request.user, "TRASH_FOLDER"):
        raise WebmailError(_("Invalid request"))
    get_imapconnector(request).empty(name)
    content = "<div class='alert alert-info'>%s</div>" % _("Empty mailbox")
    return ajax_simple_response(dict(
            status="ok", listing=content, mailbox=name
            ))

@login_required
@needs_mailbox()
def compact(request, name):
    imapc = get_imapconnector(request)
    imapc.compact(name)
    return ajax_simple_response(dict(status="ok"))

@login_required
@needs_mailbox()
def newfolder(request, tplname="webmail/folder.html"):
    mbc = IMAPconnector(user=request.user.username,
                        password=request.session["password"])
    ctx = {"title" : _("Create a new mailbox"),
           "formid" : "mboxform",
           "action" : reverse(newfolder),
           "action_label" : _("Create"),
           "action_classes" : "submit",
           "withunseen" : False,
           "selectonly" : True}

    ctx["mboxes"] = mbc.getmboxes(request.user)
    if request.method == "POST":
        form = FolderForm(request.POST)
        if form.is_valid():
            pf = request.POST.get("parent_folder", None)
            mbc.create_folder(form.cleaned_data["name"], pf)
            return ajax_simple_response(dict(
                    status="ok", respmsg=_("Mailbox created"), newmb=form.cleaned_data["name"], parent=pf
                    ))

        ctx["form"] = form
        ctx["selected"] = None
        return ajax_response(request, status="ko", template=tplname, **ctx)

    ctx["form"] = FolderForm()
    ctx["selected"] = None
    return _render(request, tplname, ctx)

@login_required
@needs_mailbox()
def editfolder(request, tplname="webmail/folder.html"):
    mbc = IMAPconnector(user=request.user.username,
                        password=request.session["password"])
    ctx = {"title" : _("Edit mailbox"),
           "formid" : "mboxform",
           "action" : reverse(editfolder),
           "action_label" : _("Update"),
           "action_classes" : "submit",
           "withunseen" : False,
           "selectonly" : True}

    if request.method == "POST":
        form = FolderForm(request.POST)
        if form.is_valid():
            pf = request.POST.has_key("parent_folder") \
                and request.POST["parent_folder"] or None
            ctx["selected"] = pf
            oldname, oldparent = separate_mailbox(request.POST["oldname"])
            res = dict(status="ok", respmsg=_("Mailbox updated"))
            if form.cleaned_data["name"] != oldname \
                    or (pf != oldparent):
                newname = form.cleaned_data["name"] if pf is None \
                    else "%s.%s" % (pf, form.cleaned_data["name"])
                mbc.rename_folder(request.POST["oldname"], newname)
                res["oldmb"] = oldname
                res["newmb"] = form.cleaned_data["name"]
                res["oldparent"] = oldparent
                res["newparent"] = pf
                del request.session["mbox"]
            return ajax_simple_response(res)

        ctx["mboxes"] = mbc.getmboxes(request.user)
        ctx["form"] = form
        return ajax_response(request, status="ko", template=tplname, **ctx)

    name = request.GET.get("name", None)
    if name is None:
        raise WebmailError(_("Invalid request"))
    shortname, parent = separate_mailbox(name)
    ctx["mboxes"] = mbc.getmboxes(request.user, until_mailbox=parent)
    ctx["form"] = FolderForm()
    ctx["form"].fields["oldname"].initial = name
    ctx["form"].fields["name"].initial = shortname
    ctx["selected"] = parent
    return _render(request, tplname, ctx)

@login_required
@needs_mailbox()
def delfolder(request):
    name = request.GET.get("name", None)
    if name is None:
        raise WebmailError(_("Bad request"))
    mbc = IMAPconnector(user=request.user.username,
                        password=request.session["password"])
    mbc.delete_folder(name)
    if request.session.has_key("mbox"):
        del request.session["mbox"]
    return ajax_response(request)

@login_required
@needs_mailbox()
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
                        })
            except WebmailError, inst:
                error = _("Failed to save attachment: ") + str(inst)

        if csuploader.toobig:
            error = _("Attachment is too big (limit: %s)" \
                          % parameters.get_admin("MAX_ATTACHMENT_SIZE"))
        return _render(request, "webmail/upload_done.html", {
                "status" : "ko", "error" : error
                })
    ctx = {
        "title" : _("Attachments"),
        "formid" : "uploadfile",
        "target" : "upload_target",
        "enctype" : "multipart/form-data",
        "form" : AttachmentForm(),
        "action" : reverse(attachments),
        "attachments" : request.session["compose_mail"]["attachments"]
        }
    return _render(request, tplname, ctx)

@login_required
@needs_mailbox()
def delattachment(request):
    if not request.session.has_key("compose_mail") \
            or not request.GET.has_key("name") \
            or not request.GET["name"]:
        return ajax_response(request, "ko", respmsg=_("Bad query"))

    error = None
    for att in request.session["compose_mail"]["attachments"]:
        if att["tmpname"] == request.GET["name"]:
            request.session["compose_mail"]["attachments"].remove(att)
            fullpath = os.path.join(settings.MEDIA_ROOT, "webmail", att["tmpname"])
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

def render_mboxes_list(request, imapc):
    """Return the HTML representation of a mailboxes list

    :param request: a ``Request`` object
    :param imapc: an ``IMAPconnector` object
    :return: a string
    """
    curmbox = request.session.get("mbox", "INBOX")
    return _render_to_string(request, "webmail/folders.html", {
            "selected" : curmbox,
            "mboxes" : imapc.getmboxes(request.user),
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

def listmailbox(request, defmailbox="INBOX", update_session=True):
    """Mailbox content listing

    Return a list of messages contained in the specified mailbox. The
    number of elements returned depends on the ``MESSAGES_PER_PAGE``
    parameter. (user preferences)

    :param request: a ``Request`` object
    :param defmailbox: the default mailbox (when not present inside request arguments)
    :return: a dictionnary
    """
    mbox = request.GET.get("mbox", defmailbox)
    if update_session:
        set_nav_params(request)
        request.session["mbox"] = mbox

    lst = ImapListing(request.user, request.session["password"],
                      baseurl="?action=listmailbox&mbox=%s&" % mbox,
                      folder=mbox,
                      elems_per_page=int(parameters.get_user(request.user, "MESSAGES_PER_PAGE")),
                      **request.session["navparams"])
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
    url = "?action=compose"
    if request.method == "POST":
        status, resp = send_mail(request, posturl=url)
        return resp

    form = ComposeMailForm()
    form.fields["from_"].initial = request.user.username
    return render_compose(request, form, url, insert_signature=True)

def compose_and_send(request, action, callback=None):
    mbox = request.GET.get("mbox", None)
    mailid = request.GET.get("mailid", None)
    if mbox is None or mailid is None:
        raise WebmailError(_("Bad request"))
    url = "?action=%s&mbox=%s&mailid=%s" % (action, mbox, mailid)
    if request.method == "POST":
        status, resp = send_mail(request, url)
        if status and callback:
            callback(mbox, mailid)
        return resp

    form = ComposeMailForm()
    modclass = globals()["%sModifier" % action.capitalize()]
    email = modclass(mbox, mailid, request, form, addrfull=True, links="1")
    return render_compose(request, form, url, email)

def reply(request):
    def msg_replied(mbox, mailid):
        get_imapconnector(request).msg_answered(mbox, mailid)

    return compose_and_send(request, "reply", msg_replied)

def forward(request):
    def msg_forwarded(mbox, mailid):
        get_imapconnector(request).msg_forwarded(mbox, mailid)

    return compose_and_send(request, "forward", msg_forwarded)

@login_required
@needs_mailbox()
def getmailcontent(request):
    mbox = request.GET.get("mbox", None)
    mailid = request.GET.get("mailid", None)
    if mbox is None or mailid is None:
         raise WebmailError(_("Invalid request"))
    email = ImapEmail(mbox, mailid, request, links=int(request.GET["links"]))
    return _render(request, "common/viewmail.html", {
            "headers" : email.render_headers(folder=mbox, mail_id=mailid),
            "folder" : mbox, "imapid" : mailid, "mailbody" : email.body if email.body else ""
            })

def viewmail(request):
    mbox = request.GET.get("mbox", None)
    mailid = request.GET.get("mailid", None)
    if mbox is None or mailid is None:
        raise WebmailError(_("Invalid request"))
    links = request.GET.get("links", None)
    if links is None:
        links = 1 if parameters.get_user(request.user, "ENABLE_LINKS") == "yes" else 0
    else:
        links = int(links)

    url = reverse(getmailcontent) + "?mbox=%s&mailid=%s&links=%d" % \
        (mbox, mailid, links)
    content = Template("""
<iframe src="{{ url }}" id="mailcontent"></iframe>
""").render(Context({"url" : url}))

    return dict(listing=content, menuargs=dict(mail_id=mailid))

@login_required
@needs_mailbox()
def submailboxes(request):
    topmailbox = request.GET.get('topmailbox', '')
    mboxes = get_imapconnector(request).getmboxes(request.user, topmailbox)
    return ajax_simple_response(dict(status="ok", mboxes=mboxes))

@login_required
@needs_mailbox()
def check_unseen_messages(request):
    mboxes = request.GET.get("mboxes", None)
    if not mboxes:
        raise WebmailError(_("Invalid request"))
    mboxes = mboxes.split(",")
    counters = dict()
    imapc = get_imapconnector(request)
    for mb in mboxes:
        counters[mb] = imapc.unseen_messages(mb)
    return ajax_simple_response(dict(status="ok", counters=counters))

@login_required
@needs_mailbox()
def index(request):
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

    if action is not None:
        if not globals().has_key(action):
            raise WebmailError(_("Undefined action"))
        response = globals()[action](request)
    else:
        if request.is_ajax():
            raise WebmailError(_("Bad request"))
        response = dict(selection="webmail")

    curmbox = request.session.get("mbox", "INBOX")
    if not request.is_ajax():
        request.session["lastaction"] = None
        imapc = get_imapconnector(request)
        response["mboxes"] = render_mboxes_list(request, imapc)
        imapc.getquota(curmbox)
        response["refreshrate"] = \
            int(parameters.get_user(request.user, "REFRESH_INTERVAL"))
        response["quota"] = ImapListing.computequota(imapc)
        response["ro_mboxes"] = ["INBOX", "Junk",
                                 parameters.get_user(request.user, "SENT_FOLDER"),
                                 parameters.get_user(request.user, "TRASH_FOLDER"),
                                 parameters.get_user(request.user, "DRAFTS_FOLDER")]

        return _render(request, "webmail/index.html", response)

    if action in ["reply", "forward"]:
        action = "compose"
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

    response.update(callback=action)
    if not response.has_key("status"):
        response.update(status="ok")
    return ajax_simple_response(response)
