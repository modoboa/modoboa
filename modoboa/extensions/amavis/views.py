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
from modoboa.lib.exceptions import BadRequest
from modoboa.lib.webutils import (
    getctx, ajax_response, render_to_json_response
)
from modoboa.lib.templatetags.lib_tags import pagination_bar
from modoboa.extensions.admin.models import Mailbox, Domain
from modoboa.extensions.amavis.templatetags.amavis_tags import (
    quar_menu, viewm_menu
)
from .lib import selfservice, AMrelease, QuarantineNavigationParameters
from .sql_listing import SQLlisting, SQLemail, get_wrapper
from .models import Msgrcpt


def empty_quarantine(request):
    content = "<div class='alert alert-info'>%s</div>" % _("Empty quarantine")
    ctx = getctx("ok", level=2, listing=content, paginbar="")
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")


@login_required
def _listing(request):
    flt = None
    rcptfilter = None
    msgs = None

    if not request.user.is_superuser and request.user.group != 'SimpleUsers':
        if not Domain.objects.get_for_admin(request.user).count():
            return empty_quarantine(request)

    navparams = QuarantineNavigationParameters(request)
    navparams.store()
    pattern = navparams.get('pattern', '')
    if pattern:
        criteria = navparams.get('criteria')
        if criteria == "both":
            criteria = "from_addr,subject,to"
        for c in criteria.split(","):
            if c == "from_addr":
                nfilter = Q(mail__from_addr__contains=pattern)
            elif c == "subject":
                nfilter = Q(mail__subject__contains=pattern)
            elif c == "to":
                rcptfilter = pattern
                continue
            else:
                raise BadRequest("unsupported search criteria %s" % c)
            flt = nfilter if flt is None else flt | nfilter

    msgtype = navparams.get('msgtype', None)
    if msgtype is not None:
        nfilter = Q(mail__msgrcpt__content=msgtype)
        flt = flt | nfilter if flt is not None else nfilter

    msgs = get_wrapper().get_mails(request, rcptfilter)
    page = navparams.get('page')
    lst = SQLlisting(
        request.user, msgs, flt,
        navparams=request.session["quarantine_navparams"],
        elems_per_page=int(parameters.get_user(request.user, "MESSAGES_PER_PAGE"))
    )
    page = lst.paginator.getpage(page)
    if not page:
        return empty_quarantine(request)

    content = lst.fetch(request, page.id_start, page.id_stop)
    paginbar = pagination_bar(page)
    ctx = getctx("ok", listing=content, paginbar=paginbar, page=page.number)
    if request.session.get('location', 'listing') != 'listing':
        ctx['menu'] = quar_menu(request.user)
    request.session['location'] = 'listing'
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")


@login_required
def index(request):
    return render(request, "amavis/index.html", dict(
        deflocation="listing/?sort_order=-date", defcallback="listing_cb",
        selection="quarantine"
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
    rcpt = request.GET["rcpt"]
    if request.user.mailbox_set.count():
        mb = Mailbox.objects.get(user=request.user)
        if rcpt in mb.alias_addresses:
            msgrcpt = get_wrapper().get_recipient_message(rcpt, mail_id)
            msgrcpt.rs = 'V'
            msgrcpt.save()

    content = Template("""
<iframe src="{{ url }}" id="mailcontent"></iframe>
""").render(Context({"url": reverse(getmailcontent, args=[mail_id])}))
    menu = viewm_menu(mail_id, rcpt)
    ctx = getctx("ok", menu=menu, listing=content)
    request.session['location'] = 'viewmail'
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")


@login_required
def viewheaders(request, mail_id):
    content = ""
    for qm in get_wrapper().get_mail_content(mail_id):
        content += qm.mail_text
    msg = email.message_from_string(content)
    return render(request, 'amavis/viewheader.html', {
        "headers": msg.items()
    })


def check_mail_id(request, mail_id):
    if type(mail_id) in [str, unicode]:
        if "rcpt" in request.POST:
            mail_id = ["%s %s" % (request.POST["rcpt"], mail_id)]
        else:
            mail_id = [mail_id]
    return mail_id


def delete_selfservice(request, mail_id):
    rcpt = request.GET.get("rcpt", None)
    if rcpt is None:
        raise BadRequest(_("Invalid request"))
    try:
        msgrcpt = get_wrapper().get_recipient_message(rcpt, mail_id)
        msgrcpt.rs = 'D'
        msgrcpt.save()
    except Msgrcpt.DoesNotExist:
        raise BadRequest(_("Invalid request"))
    return render_to_json_response(_("Message deleted"))


@selfservice(delete_selfservice)
def delete(request, mail_id):
    mail_id = check_mail_id(request, mail_id)
    wrapper = get_wrapper()
    mb = Mailbox.objects.get(user=request.user) \
        if request.user.group == 'SimpleUsers' else None
    for mid in mail_id:
        r, i = mid.split()
        if mb is not None and not r in mb.alias_addresses:
            continue
        msgrcpt = wrapper.get_recipient_message(r, i)
        msgrcpt.rs = 'D'
        msgrcpt.save()
    message = ungettext("%(count)d message deleted successfully",
                        "%(count)d messages deleted successfully",
                        len(mail_id)) % {"count": len(mail_id)}
    return ajax_response(
        request, respmsg=message,
        url=QuarantineNavigationParameters(request).back_to_listing()
    )


def release_selfservice(request, mail_id):
    rcpt = request.GET.get("rcpt", None)
    secret_id = request.GET.get("secret_id", None)
    if rcpt is None or secret_id is None:
        raise BadRequest(_("Invalid request"))
    try:
        msgrcpt = get_wrapper().get_recipient_message(rcpt, mail_id)
    except Msgrcpt.DoesNotExist:
        raise BadRequest(_("Invalid request"))
    if secret_id != msgrcpt.mail.secret_id:
        raise BadRequest(_("Invalid request"))
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
            raise BadRequest(result)
    msgrcpt.save()
    return render_to_json_response(msg)


@selfservice(release_selfservice)
def release(request, mail_id):
    """Release message selection.

    :param str mail_id: message unique identifier
    """
    mail_id = check_mail_id(request, mail_id)
    msgrcpts = []
    wrapper = get_wrapper()
    mb = Mailbox.objects.get(user=request.user) \
        if request.user.group == 'SimpleUsers' else None
    for mid in mail_id:
        r, i = mid.split()
        if mb is not None and not r in mb.alias_addresses:
            continue
        msgrcpts += [wrapper.get_recipient_message(r, i)]
    if mb is not None and parameters.get_admin("USER_CAN_RELEASE") == "no":
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
        return ajax_response(
            request, "ok", respmsg=message,
            url=QuarantineNavigationParameters(request).back_to_listing()
        )

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
    return ajax_response(
        request, "ko" if error else "ok", respmsg=message,
        url=QuarantineNavigationParameters(request).back_to_listing()
    )


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
    return render_to_json_response({'requests': result})
