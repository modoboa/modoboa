# coding: utf-8
"""
Webmail extension views.
"""

import os

from rfc6266 import build_header

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.template import Template, Context
from django.utils.translation import ugettext as _, ungettext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page

from modoboa.lib import parameters
from modoboa.lib.exceptions import ModoboaException, BadRequest
from modoboa.lib.paginator import Paginator
from modoboa.lib.webutils import (
    _render_to_string, ajax_response, render_to_json_response
)
from modoboa.extensions.admin.lib import needs_mailbox
from .exceptions import UnknownAction
from .forms import (
    FolderForm, AttachmentForm, ComposeMailForm, ForwardMailForm
)
from .lib import (
    decode_payload, AttachmentUploadHandler,
    save_attachment, EmailSignature,
    clean_attachments, set_compose_session, send_mail,
    ImapEmail, WebmailNavigationParameters, ReplyModifier, ForwardModifier,
    get_imapconnector, IMAPconnector, separate_mailbox
)
from .templatetags import webmail_tags


@login_required
@needs_mailbox()
@gzip_page
def getattachment(request):
    """Fetch a message attachment

    FIXME: par manque de caching, le bodystructure du message est
    redemandé pour accéder aux headers de cette pièce jointe.

    :param request: a ``Request`` object
    """
    mbox = request.GET.get("mbox", None)
    mailid = request.GET.get("mailid", None)
    pnum = request.GET.get("partnumber", None)
    fname = request.GET.get("fname", None)
    if not mbox or not mailid or not pnum or not fname:
        raise BadRequest(_("Invalid request"))

    imapc = get_imapconnector(request)
    partdef, payload = imapc.fetchpart(mailid, mbox, pnum)
    resp = HttpResponse(decode_payload(partdef["encoding"], payload))
    resp["Content-Type"] = partdef["Content-Type"]
    resp["Content-Transfer-Encoding"] = partdef["encoding"]
    resp["Content-Disposition"] = build_header(fname)
    if int(partdef["size"]) < 200:
        resp["Content-Length"] = partdef["size"]
    return resp


@login_required
@needs_mailbox()
def move(request):
    for arg in ["msgset", "to"]:
        if not arg in request.GET:
            raise BadRequest(_("Invalid request"))
    mbc = get_imapconnector(request)
    navparams = WebmailNavigationParameters(request)
    mbc.move(request.GET["msgset"], navparams.get('mbox'), request.GET["to"])
    resp = listmailbox(request, navparams.get('mbox'), update_session=False)
    return render_to_json_response(resp)


@login_required
@needs_mailbox()
def delete(request):
    mbox = request.GET.get("mbox", None)
    selection = request.GET.getlist("selection[]", None)
    if mbox is None or selection is None:
        raise BadRequest(_("Invalid request"))
    selection = [item for item in selection if item.isdigit()]
    mbc = get_imapconnector(request)
    mbc.move(",".join(selection), mbox,
             parameters.get_user(request.user, "TRASH_FOLDER"))
    count = len(selection)
    message = ungettext("%(count)d message deleted",
                        "%(count)d messages deleted",
                        count) % {"count": count}
    return render_to_json_response(message)


@login_required
@needs_mailbox()
def mark(request, name):
    status = request.GET.get("status", None)
    ids = request.GET.get("ids", None)
    if status is None or ids is None:
        raise BadRequest(_("Invalid request"))
    imapc = get_imapconnector(request)
    try:
        getattr(imapc, "mark_messages_%s" % status)(name, ids)
    except AttributeError:
        raise UnknownAction

    return render_to_json_response({
        'action': status, 'mbox': name,
        'unseen': imapc.unseen_messages(name)
    })


@login_required
@needs_mailbox()
def empty(request):
    """Empty the trash folder."""
    name = request.GET.get("name", None)
    if name != parameters.get_user(request.user, "TRASH_FOLDER"):
        raise BadRequest(_("Invalid request"))
    get_imapconnector(request).empty(name)
    content = "<div class='alert alert-info'>%s</div>" % _("Empty mailbox")
    return render_to_json_response({
        'listing': content, 'mailbox': name, 'pages': [1]
    })


@login_required
@needs_mailbox()
def folder_compress(request):
    """Compress a mailbox."""
    name = request.GET.get("name", None)
    if name is None:
        raise BadRequest(_("Invalid request"))
    imapc = get_imapconnector(request)
    imapc.compact(name)
    return render_to_json_response({})


@login_required
@needs_mailbox()
def newfolder(request, tplname="webmail/folder.html"):
    mbc = IMAPconnector(user=request.user.username,
                        password=request.session["password"])

    if request.method == "POST":
        form = FolderForm(request.POST)
        if form.is_valid():
            pf = request.POST.get("parent_folder", None)
            mbc.create_folder(form.cleaned_data["name"], pf)
            return render_to_json_response({
                'respmsg': _("Mailbox created"),
                'newmb': form.cleaned_data["name"], 'parent': pf
            })

        return render_to_json_response({'form_errors': form.errors}, status=400)

    ctx = {"title": _("Create a new mailbox"),
           "formid": "mboxform",
           "action": reverse("webmail:folder_add"),
           "action_label": _("Create"),
           "action_classes": "submit",
           "withunseen": False,
           "selectonly": True,
           "mboxes": mbc.getmboxes(request.user),
           "hdelimiter": mbc.hdelimiter,
           "form": FolderForm(),
           "selected": None}
    return render(request, tplname, ctx)


@login_required
@needs_mailbox()
def editfolder(request, tplname="webmail/folder.html"):
    mbc = IMAPconnector(user=request.user.username,
                        password=request.session["password"])
    ctx = {"title": _("Edit mailbox"),
           "formid": "mboxform",
           "action": reverse("webmail:folder_change"),
           "action_label": _("Update"),
           "action_classes": "submit",
           "withunseen": False,
           "selectonly": True,
           "hdelimiter": mbc.hdelimiter}

    if request.method == "POST":
        form = FolderForm(request.POST)
        if form.is_valid():
            pf = request.POST.get("parent_folder", None)
            oldname, oldparent = separate_mailbox(
                request.POST["oldname"], sep=mbc.hdelimiter
            )
            res = {'respmsg': _("Mailbox updated")}
            if form.cleaned_data["name"] != oldname \
                    or (pf != oldparent):
                newname = form.cleaned_data["name"] if pf is None \
                    else mbc.hdelimiter.join([pf, form.cleaned_data["name"]])
                mbc.rename_folder(request.POST["oldname"], newname)
                res["oldmb"] = oldname
                res["newmb"] = form.cleaned_data["name"]
                res["oldparent"] = oldparent
                res["newparent"] = pf
                WebmailNavigationParameters(request).remove('mbox')
            return render_to_json_response(res)

        return render_to_json_response({'form_errors': form.errors}, status=400)

    name = request.GET.get("name", None)
    if name is None:
        raise BadRequest(_("Invalid request"))
    shortname, parent = separate_mailbox(name, sep=mbc.hdelimiter)
    ctx = {"title": _("Edit mailbox"),
           "formid": "mboxform",
           "action": reverse("webmail:folder_change"),
           "action_label": _("Update"),
           "action_classes": "submit",
           "withunseen": False,
           "selectonly": True,
           "hdelimiter": mbc.hdelimiter,
           "mboxes": mbc.getmboxes(request.user, until_mailbox=parent),
           "form": FolderForm(),
           "selected": parent}
    ctx["form"].fields["oldname"].initial = name
    ctx["form"].fields["name"].initial = shortname
    return render(request, tplname, ctx)


@login_required
@needs_mailbox()
def delfolder(request):
    name = request.GET.get("name", None)
    if name is None:
        raise BadRequest(_("Invalid request"))
    mbc = IMAPconnector(user=request.user.username,
                        password=request.session["password"])
    mbc.delete_folder(name)
    WebmailNavigationParameters(request).remove('mbox')
    return ajax_response(request)


@login_required
@csrf_exempt
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
                    += [{"fname": str(fobj),
                         "content-type": fobj.content_type,
                         "size": fobj.size,
                         "tmpname": os.path.basename(tmpname)}]
                request.session.modified = True
                return render(request, "webmail/upload_done.html", {
                    "status": "ok", "fname": request.FILES["attachment"],
                    "tmpname": os.path.basename(tmpname)
                })
            except ModoboaException as inst:
                error = _("Failed to save attachment: ") + str(inst)

        if csuploader.toobig:
            error = _("Attachment is too big (limit: %s)"
                      % parameters.get_admin("MAX_ATTACHMENT_SIZE"))
        return render(request, "webmail/upload_done.html", {
            "status": "ko", "error": error
        })
    ctx = {
        "title": _("Attachments"),
        "formid": "uploadfile",
        "target": "upload_target",
        "enctype": "multipart/form-data",
        "form": AttachmentForm(),
        "action": reverse("webmail:attachment_list"),
        "attachments": request.session["compose_mail"]["attachments"]
    }
    return render(request, tplname, ctx)


@login_required
@needs_mailbox()
def delattachment(request):
    if not "compose_mail" in request.session \
            or not "name" in request.GET \
            or not request.GET["name"]:
        return ajax_response(request, "ko", respmsg=_("Bad query"))

    error = None
    for att in request.session["compose_mail"]["attachments"]:
        if att["tmpname"] == request.GET["name"]:
            request.session["compose_mail"]["attachments"].remove(att)
            fullpath = os.path.join(
                settings.MEDIA_ROOT, "webmail", att["tmpname"]
            )
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
    curmbox = WebmailNavigationParameters(request).get("mbox", "INBOX")
    return _render_to_string(request, "webmail/folders.html", {
        "selected": curmbox,
        "mboxes": imapc.getmboxes(request.user),
        "withunseen": True
    })


def listmailbox(request, defmailbox="INBOX", update_session=True):
    """Mailbox content listing.

    Return a list of messages contained in the specified mailbox. The
    number of elements returned depends on the ``MESSAGES_PER_PAGE``
    parameter. (user preferences)

    :param request: a ``Request`` object
    :param defmailbox: the default mailbox (when not present inside
                       request arguments)
    :return: a dictionnary
    """
    navparams = WebmailNavigationParameters(request, defmailbox)
    previous_page_id = int(navparams["page"]) if "page" in navparams else None
    if update_session:
        navparams.store()
    mbox = navparams.get('mbox')
    page_id = int(navparams["page"])
    mbc = get_imapconnector(request)
    mbc.parse_search_parameters(
        navparams.get("criteria"), navparams.get("pattern"))

    paginator = Paginator(
        mbc.messages_count(folder=mbox, order=navparams.get("order")),
        int(parameters.get_user(request.user, "MESSAGES_PER_PAGE"))
    )
    page = paginator.getpage(page_id)
    content = ""
    if page is not None:
        email_list = mbc.fetch(page.id_start, page.id_stop, mbox)
        content = _render_to_string(request, "webmail/email_list.html", {
            "email_list": email_list,
            "page": page_id,
            "with_top_div": request.GET.get("scroll", "false") == "false"
        })
        length = len(content)
    else:
        if page_id == 1:
            content = "<div class='alert alert-info'>{0}</div>".format(
                _("Empty mailbox")
            )
        length = 0
        if previous_page_id is not None:
            navparams["page"] = previous_page_id
    return {"listing": content, "length": length, "pages": [page_id]}


def render_compose(request, form, posturl, email=None, insert_signature=False):
    """Render the compose form."""
    resp = {}
    if email is None:
        body = u""
        textheader = u""
    else:
        body = email.body
        textheader = email.textheader
    if insert_signature:
        signature = EmailSignature(request.user)
        body += unicode(signature)
    randid = None
    if not "id" in request.GET:
        if "compose_mail" in request.session:
            clean_attachments(request.session["compose_mail"]["attachments"])
        randid = set_compose_session(request)
    elif not "compose_mail" in request.session \
            or request.session["compose_mail"]["id"] != request.GET["id"]:
        randid = set_compose_session(request)

    attachment_list = request.session["compose_mail"]["attachments"]
    if attachment_list:
        resp["menuargs"] = {"attachment_counter": len(attachment_list)}

    content = _render_to_string(request, "webmail/compose.html", {
        "form": form, "bodyheader": textheader,
        "body": body, "posturl": posturl
    })

    resp.update({
        "listing": content,
        "editor": parameters.get_user(request.user, "EDITOR")
    })
    if randid is not None:
        resp["id"] = randid
    return resp


def compose(request):
    url = "?action=compose"
    if request.method == "POST":
        form = ComposeMailForm(request.POST)
        status, resp = send_mail(request, form, posturl=url)
        return resp

    form = ComposeMailForm()
    return render_compose(request, form, url, insert_signature=True)


def get_mail_info(request):
    """Retrieve a mailbox and an email ID from a request.
    """
    mbox = request.GET.get("mbox", None)
    mailid = request.GET.get("mailid", None)
    if mbox is None or mailid is None:
        raise BadRequest(_("Invalid request"))
    return mbox, mailid


def new_compose_form(request, action, mbox, mailid):
    """Return a new composition form.

    Valid for reply and forward actions only.
    """
    form = ComposeMailForm()
    modclass = globals()["%sModifier" % action.capitalize()]
    email = modclass(form, request, True, "%s:%s" % (mbox, mailid), links="1")
    url = "?action=%s&mbox=%s&mailid=%s" % (action, mbox, mailid)
    return render_compose(request, form, url, email)


def reply(request):
    """Reply to email.
    """
    mbox, mailid = get_mail_info(request)
    if request.method == "POST":
        url = "?action=reply&mbox=%s&mailid=%s" % (mbox, mailid)
        form = ComposeMailForm(request.POST)
        status, resp = send_mail(request, form, url)
        if status:
            get_imapconnector(request).msg_answered(mbox, mailid)
        return resp
    return new_compose_form(request, "reply", mbox, mailid)


def forward(request):
    """Forward email.
    """
    mbox, mailid = get_mail_info(request)
    if request.method == "POST":
        url = "?action=forward&mbox=%s&mailid=%s" % (mbox, mailid)
        form = ForwardMailForm(request.POST)
        status, resp = send_mail(request, form, url)
        if status:
            get_imapconnector(request).msg_forwarded(mbox, mailid)
        return resp
    return new_compose_form(request, "forward", mbox, mailid)


@login_required
@needs_mailbox()
def getmailcontent(request):
    mbox = request.GET.get("mbox", None)
    mailid = request.GET.get("mailid", None)
    if mbox is None or mailid is None:
        raise BadRequest(_("Invalid request"))
    email = ImapEmail(
        request, False, "%s:%s" % (mbox, mailid), dformat="DISPLAYMODE",
        links=int(request.GET["links"])
    )
    return render(request, "common/viewmail.html", {
        "headers": email.render_headers(folder=mbox, mail_id=mailid),
        "folder": mbox, "imapid": mailid,
        "mailbody": email.body if email.body else ""
    })


def viewmail(request):
    mbox = request.GET.get("mbox", None)
    mailid = request.GET.get("mailid", None)
    if mbox is None or mailid is None:
        raise BadRequest(_("Invalid request"))
    links = request.GET.get("links", None)
    if links is None:
        links = 1 if parameters.get_user(
            request.user, "ENABLE_LINKS") == "yes" else 0
    else:
        links = int(links)

    url = "{0}?mbox={1}&mailid={2}&links={3}".format(
        reverse("webmail:mailcontent_get"), mbox, mailid, links)
    content = Template("""
<iframe src="{{ url }}" id="mailcontent"></iframe>
""").render(Context({"url": url}))

    return dict(listing=content, menuargs=dict(mail_id=mailid))


@login_required
@needs_mailbox()
def submailboxes(request):
    """Retrieve the sub mailboxes of a mailbox."""
    topmailbox = request.GET.get('topmailbox', '')
    with_unseen = request.GET.get('unseen', None)
    mboxes = get_imapconnector(request).getmboxes(
        request.user, topmailbox, unseen_messages=with_unseen == 'true')
    return render_to_json_response(mboxes)


@login_required
@needs_mailbox()
def check_unseen_messages(request):
    mboxes = request.GET.get("mboxes", None)
    if not mboxes:
        raise BadRequest(_("Invalid request"))
    mboxes = mboxes.split(",")
    counters = dict()
    imapc = get_imapconnector(request)
    for mb in mboxes:
        counters[mb] = imapc.unseen_messages(mb)
    return render_to_json_response(counters)


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
        if not action in globals():
            raise UnknownAction
        response = globals()[action](request)
    else:
        if request.is_ajax():
            raise BadRequest(_("Invalid request"))
        response = dict(selection="webmail")

    curmbox = WebmailNavigationParameters(request).get("mbox", "INBOX")
    if not request.is_ajax():
        request.session["lastaction"] = None
        imapc = get_imapconnector(request)
        response["hdelimiter"] = imapc.hdelimiter
        response["mboxes"] = render_mboxes_list(request, imapc)
        imapc.getquota(curmbox)
        response["refreshrate"] = \
            int(parameters.get_user(request.user, "REFRESH_INTERVAL"))
        response["quota"] = imapc.quota_usage
        trash = parameters.get_user(request.user, "TRASH_FOLDER")
        response["trash"] = trash
        response["ro_mboxes"] = [
            "INBOX", "Junk",
            parameters.get_user(request.user, "SENT_FOLDER"),
            trash,
            parameters.get_user(request.user, "DRAFTS_FOLDER")
        ]
        response['mboxes_col_width'] = \
            int(parameters.get_user(request.user, 'MBOXES_COL_WIDTH'))
        return render(request, "webmail/index.html", response)

    if action in ["reply", "forward"]:
        action = "compose"
    if request.session["lastaction"] != action:
        extra_args = {}
        if "menuargs" in response:
            extra_args = response["menuargs"]
            del response["menuargs"]
        try:
            menu = getattr(webmail_tags, "%s_menu" % action)
            response["menu"] = menu("", curmbox, request.user, **extra_args)
        except KeyError:
            pass

    response.update(callback=action)
    http_status = 200
    if "status" in response:
        del response['status']
        http_status = 400
    return render_to_json_response(response, status=http_status)
