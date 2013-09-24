# coding: utf-8
import email
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.template import Template, Context
from django.utils import simplejson
from django.utils.translation import ugettext as _, ungettext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators \
    import login_required, user_passes_test
from django.db.models import Q
from modoboa.lib import parameters
from modoboa.lib.exceptions import ModoboaException
from modoboa.lib.webutils import (
    getctx, ajax_response, ajax_simple_response
)
from modoboa.lib.email_listing import parse_search_parameters
from modoboa.extensions.admin.models import Mailbox
from templatetags.amextras import quar_menu, viewm_menu
from .lib import selfservice, AMrelease
from .sql_listing import SQLlisting, SQLemail, get_wrapper


def __back_to_listing(request):
    """Return the current listing URL.

    Looks into the user's session and the current request to build the
    URL.

    :param request: a ``Request`` object
    :return: a string
    """
    url = "listing"
    params = []
    if "page" in request.session:
        params += ["page=%s" % request.session["page"]]

    params += ["%s=%s" % (p, request.session[p])
               for p in ["criteria", "pattern"] if p in request.session]
    if params:
        url += "?%s" % ("&".join(params))
    return url


def empty_quarantine(request):
    content = "<div class='alert alert-info'>%s</div>" % _("Empty quarantine")
    ctx = getctx("ok", level=2, listing=content, navbar="",
                 menu=quar_menu(request.user))
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")


@login_required
def _listing(request):
    flt = None
    rcptfilter = None
    msgs = None

    if not request.user.is_superuser and request.user.group != 'SimpleUsers':
        if not len(request.user.get_domains()):
            return empty_quarantine(request)

    order = request.GET.get("order", "-date")
    if not "navparams" in request.session:
        request.session["navparams"] = {}
    request.session["navparams"]["order"] = order

    parse_search_parameters(request)
    if "pattern" in request.session:
        criteria = request.session["criteria"]
        if criteria == "both":
            criteria = "from_addr,subject,to"
        for c in criteria.split(","):
            if c == "from_addr":
                nfilter = Q(mail__from_addr__contains=request.session["pattern"])
            elif c == "subject":
                nfilter = Q(mail__subject__contains=request.session["pattern"])
            elif c == "to":
                rcptfilter = request.session["pattern"]
                continue
            else:
                raise Exception("unsupported search criteria %s" % c)
            flt = nfilter if flt is None else flt | nfilter

    msgs = get_wrapper().get_mails(request, rcptfilter)

    if "page" in request.GET:
        request.session["page"] = request.GET["page"]
        pageid = int(request.session["page"])
    else:
        if "page" in request.session:
            del request.session["page"]
        pageid = 1

    lst = SQLlisting(
        request.user, msgs, flt,
        navparams=request.session["navparams"],
        elems_per_page=int(parameters.get_user(request.user, "MESSAGES_PER_PAGE"))
    )
    page = lst.paginator.getpage(pageid)
    if not page:
        return empty_quarantine(request)

    content = lst.fetch(request, page.id_start, page.id_stop)
    navbar = lst.render_navbar(page, "listing/?")
    ctx = getctx("ok", listing=content, navbar=navbar,
                 menu=quar_menu(request.user))
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")


@login_required
def index(request):
    return render(request, "amavis/index.html", dict(
        deflocation="listing/", defcallback="listing_cb", selection="quarantine"
    ))


def getmailcontent_selfservice(request, mail_id):
    qmails = get_wrapper().get_mail_content(mail_id)
    content = ""
    for qm in qmails:
        content += qm.mail_text
    msg = email.message_from_string(content)
    mail = SQLemail(msg, mformat="plain", links="0")
    return render(request, "common/viewmail.html", {
        "headers": mail.render_headers(),
        "mailbody": mail.body
    })


@selfservice(getmailcontent_selfservice)
def getmailcontent(request, mail_id):
    qmails = get_wrapper().get_mail_content(mail_id)
    content = ""
    for qm in qmails:
        content += qm.mail_text
    msg = email.message_from_string(content)
    mail = SQLemail(msg, mformat="plain", links="0")
    return render(request, "common/viewmail.html", {
        "headers": mail.render_headers(),
        "mailbody": mail.body
    })


def viewmail_selfservice(request, mail_id,
                         tplname="amavis/viewmail_selfservice.html"):
    rcpt = request.GET.get("rcpt", None)
    secret_id = request.GET.get("secret_id", "")
    if rcpt is None:
        raise Http404
    content = Template("""{% load url from future %}
<iframe src="{% url 'modoboa.extensions.amavis.views.getmailcontent' mail_id %}" id="mailcontent"></iframe>
""").render(Context(dict(mail_id=mail_id)))

    return render(request, tplname, dict(
        mail_id=mail_id, rcpt=rcpt, secret_id=secret_id, content=content
    ))


@selfservice(viewmail_selfservice)
def viewmail(request, mail_id):
    if request.user.group != 'SimpleUsers':
        rcpt = request.GET["rcpt"]
    else:
        rcpt = None

    if request.user.mailbox_set.count():
        mb = Mailbox.objects.get(user=request.user)
        if not rcpt or rcpt == mb.full_address:
            msgrcpt = get_wrapper().get_recipient_message(mb.full_address, mail_id)
            msgrcpt.rs = 'V'
            msgrcpt.save()

    content = Template("""
<iframe src="{{ url }}" id="mailcontent"></iframe>
""").render(Context({"url": reverse(getmailcontent, args=[mail_id])}))
    menu = viewm_menu(request.user, mail_id, rcpt)
    ctx = getctx("ok", menu=menu, listing=content)
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")


@login_required
def viewheaders(request, mail_id):
    content = ""
    for qm in get_wrapper().get_mail_content(mail_id):
        content += qm.mail_text
    msg = email.message_from_string(content)
    return _render(request, 'amavis/viewheader.html', {
        "headers": msg.items()
    })


def check_mail_id(request, mail_id):
    if type(mail_id) in [str, unicode]:
        if "rcpt" in request.GET:
            mail_id = ["%s %s" % (request.GET["rcpt"], mail_id)]
        else:
            mail_id = [mail_id]
    return mail_id


def delete_selfservice(request, mail_id):
    rcpt = request.GET.get("rcpt", None)
    if rcpt is None:
        raise ModoboaException(_("Invalid request"))
    try:
        msgrcpt = get_wrapper().get_recipient_message(rcpt, mail_id)
        msgrcpt.rs = 'D'
        msgrcpt.save()
    except Msgrcpt.DoesNotExist:
        raise ModoboaException(_("Invalid request"))
    return ajax_simple_response(dict(status="ok", respmsg=_("Message deleted")))


@selfservice(delete_selfservice)
def delete(request, mail_id):
    mail_id = check_mail_id(request, mail_id)
    if request.user.group == 'SimpleUsers':
        mb = Mailbox.objects.get(user=request.user)
        msgrcpts = get_wrapper().get_recipient_messages(mb.full_address, mail_id)
        #msgrcpts.update(rs='D')
        for msgrcpt in msgrcpts:
            msgrcpt.rs = 'D'
            msgrcpt.save()
    else:
        wrapper = get_wrapper()
        for mid in mail_id:
            r, i = mid.split()
            msgrcpt = wrapper.get_recipient_message(r, i)
            msgrcpt.rs = 'D'
            msgrcpt.save()

    message = ungettext("%(count)d message deleted successfully",
                        "%(count)d messages deleted successfully",
                        len(mail_id)) % {"count": len(mail_id)}
    return ajax_response(request, respmsg=message,
                         url=__back_to_listing(request))


def release_selfservice(request, mail_id):
    rcpt = request.GET.get("rcpt", None)
    secret_id = request.GET.get("secret_id", None)
    if rcpt is None or secret_id is None:
        raise ModoboaException(_("Invalid request"))
    try:
        msgrcpt = get_wrapper().get_recipient_message(rcpt, mail_id)
    except Msgrcpt.DoesNotExist:
        raise ModoboaException(_("Invalid request"))
    if secret_id != msgrcpt.mail.secret_id:
        raise ModoboaException(_("Invalid request"))
    if parameters.get_admin("USER_CAN_RELEASE") == "no":
        msgrcpt.rs = 'p'
        msg = _("Request sent")
    else:
        amr = AMrelease()
        result = amr.sendreq(mail_id, secret_id, rcpt)
        if result:
            rcpt.rs = 'R'
            msg = _("Message released")
        else:
            raise ModoboaException(result)
    msgrcpt.save()
    return ajax_simple_response(dict(status="ok", respmsg=msg))


@selfservice(release_selfservice)
def release(request, mail_id):
    mail_id = check_mail_id(request, mail_id)
    if request.user.group == 'SimpleUsers':
        mb = Mailbox.objects.get(user=request.user)
        msgrcpts = get_wrapper().get_recipient_messages(mb.full_address, mail_id)
        if parameters.get_admin("USER_CAN_RELEASE") == "no":
            # FIXME : can't use this syntax because extra SQL (using
            # .extra() for postgres) is not propagated (the 'tables'
            # parameter is lost somewhere...)
            #
            # msgrcpts.update(rs='p')
            for msgrcpt in msgrcpts:
                msgrcpt.rs = 'p'
                msgrcpt.save()
            message = ungettext("%(count)d request sent",
                                "%(count)d requests sent",
                                len(mail_id)) % {"count": len(mail_id)}
            return ajax_response(request, "ok", respmsg=message,
                                 url=__back_to_listing(request))
    else:
        msgrcpts = []
        wrapper = get_wrapper()
        for mid in mail_id:
            r, i = mid.split()
            msgrcpts += [wrapper.get_recipient_message(r, i)]

    amr = AMrelease()
    error = None
    for rcpt in msgrcpts:
        result = amr.sendreq(rcpt.mail.mail_id, rcpt.mail.secret_id, rcpt.rid.email)
        if result:
            rcpt.rs = 'R'
            rcpt.save()
        else:
            error = result
            break

    if not error:
        message = ungettext("%(count)d message released successfully",
                            "%(count)d messages released successfully",
                            len(mail_id)) % {"count": len(mail_id)}
    else:
        message = error
    return ajax_response(request, "ko" if error else "ok", respmsg=message,
                         url=__back_to_listing(request))


@login_required
def process(request):
    ids = request.POST.get("selection", "")
    ids = ids.split(",")
    if not len(ids):
        return HttpResponseRedirect(reverse(index))

    if request.POST["action"] == "release":
        return release(request, ids)

    if request.POST["action"] == "delete":
        return delete(request, ids)


@login_required
@user_passes_test(lambda u: u.group != 'SimpleUsers')
def nbrequests(request):
    result = get_wrapper().get_pending_requests(request.user)
    return ajax_simple_response(dict(status="ok", requests=result))
