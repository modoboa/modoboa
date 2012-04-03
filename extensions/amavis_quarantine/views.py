# coding: utf-8
import email
from django.http import HttpResponseRedirect, HttpResponse
from django.template import Template, Context
from django.utils import simplejson
from django.utils.translation import ugettext as _, ungettext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators \
    import login_required
from django.db.models import Q
from modoboa.lib import parameters
from modoboa.lib.webutils import _render, getctx, ajax_response
from modoboa.admin.models import Mailbox
from lib import AMrelease
from templatetags.amextras import *
from modoboa.lib.email_listing import parse_search_parameters
from sql_listing import *

def __get_current_url(request):
    if request.session.has_key("page"):
        res = "?page=%s" % request.session["page"]
    else:
        res = ""
    params = "&".join(map(lambda p: "%s=%s" % (p, request.session[p]), 
                          filter(request.session.has_key, ["criteria", "pattern"])))
    if params != "":
        res += "?%s" % (params)
    return res

def empty_quarantine(request):
    content = "<div class='alert alert-info'>%s</div>" % _("Empty quarantine")
    ctx = getctx("ok", level=2, listing=content, navbar="",
                 menu=quar_menu(request.user, -1))
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
def _listing(request):
    flt = None
    rcptfilter = None
    msgs = None
    nbrequests = -1

    if not request.user.is_superuser and request.user.group != 'SimpleUsers':
        if not len(request.user.get_domains()):
            return empty_quarantine(request)

    order = request.GET.get("order", "-date")
    if not request.session.has_key("navparams"):
        request.session["navparams"] = {}
    request.session["navparams"]["order"] = order

    parse_search_parameters(request)
    if request.session.has_key("pattern"):
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

    if request.GET.get("viewrequests", None) == "1":
        q = Q(rs='p')
    else:
        q = ~Q(rs='D')
    rq = Q(rs='p')
    if request.user.group == 'SimpleUsers':
        q &= Q(rid__email=request.user.email)
    else:
        if not request.user.is_superuser:
            doms = request.user.get_domains()
            regexp = "(%s)" % '|'.join(map(lambda dom: dom.name, doms))
            doms_q = Q(rid__email__regex=regexp)
            q &= doms_q
            rp &= doms_q            
        if rcptfilter is not None:
            q &= Q(rid__email__contains=rcptfilter)

        if parameters.get_admin("USER_CAN_RELEASE") == "no":
            nbrequests = len(Msgrcpt.objects.filter(rq))

    msgs = Msgrcpt.objects.filter(q).values("mail_id")

    if request.GET.has_key("page"):
        request.session["page"] = request.GET["page"]
        pageid = int(request.session["page"])
    else:
        if request.session.has_key("page"):
            del request.session["page"]
        pageid = 1
    
    lst = SQLlisting(request.user, msgs, flt,
                     navparams=request.session["navparams"],
                     elems_per_page=int(parameters.get_user(request.user, 
                                                        "MESSAGES_PER_PAGE")))
    page = lst.paginator.getpage(pageid)
    if not page:
        return empty_quarantine(request)

    content = lst.fetch(request, page.id_start, page.id_stop)
    navbar = lst.render_navbar(page, "listing/?")
    ctx = getctx("ok", listing=content, navbar=navbar,
                 menu=quar_menu(request.user, nbrequests))
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
def index(request):
    return _render(request, "amavis_quarantine/index.html", dict(
            deflocation="listing/", defcallback="listing_cb", selection="quarantine"
            ))

@login_required
def getmailcontent(request, mail_id):
    from sql_listing import SQLemail

    qmails = Quarantine.objects.filter(mail=mail_id)
    content = ""
    for qm in qmails:
        content += qm.mail_text
    msg = email.message_from_string(content)
    links = request.GET.has_key("links") and request.GET["links"] or "0"
    mode = request.GET.has_key("mode") and request.GET["mode"] or "plain"
    mail = SQLemail(msg, mformat=mode, links=links)
    return _render(request, "common/viewmail.html", {
            "headers" : mail.render_headers(), 
            "mailbody" : mail.body
            })

@login_required
def viewmail(request, mail_id):
    if request.user.group != 'SimpleUsers':
        rcpt = request.GET["rcpt"]
    else:
        rcpt = None
        mb = Mailbox.objects.get(user=request.user)
        msgrcpt = Msgrcpt.objects.get(mail=mail_id, rid__email=mb.full_address)
        msgrcpt.rs = 'V'
        msgrcpt.save()
    args = []
    for kw in ["mode", "links"]:
        if request.GET.has_key(kw):
            args += ["%s=%s" % (kw, request.GET[kw])]
    
    content = Template("""
<iframe src="{{ url }}" id="mailcontent"></iframe>
""").render(Context({"url" : reverse(getmailcontent, args=[mail_id]) \
                         + "?%s" % "&".join(args)}))
    menu = viewm_menu(request.user, mail_id, rcpt)
    ctx = getctx("ok", menu=menu, listing=content)
    return HttpResponse(simplejson.dumps(ctx), mimetype="application/json")

@login_required
def viewheaders(request, mail_id):
    content = ""
    for qm in Quarantine.objects.filter(mail=mail_id):
        content += qm.mail_text
    msg = email.message_from_string(content)
    return _render(request, 'amavis_quarantine/viewheader.html', {
            "title" : _("Message headers"),
            "headers" : msg.items()
            })

def check_mail_id(request, mail_id):
    if type(mail_id) in [str, unicode]:
        if request.GET.has_key("rcpt"):
            mail_id = ["%s %s" % (request.GET["rcpt"], mail_id)]
        else:
            mail_id = [mail_id]
    return mail_id

@login_required
def delete(request, mail_id):
    mail_id = check_mail_id(request, mail_id)
    if request.user.group == 'SimpleUsers':
        mb = Mailbox.objects.get(user=request.user)
        msgrcpts = Msgrcpt.objects.filter(mail__in=mail_id, rid__email=mb.full_address)
        msgrcpts.update(rs='D')
    else:
        for mid in mail_id:
            r, i = mid.split()
            msgrcpt = Msgrcpt.objects.get(mail=i, rid__email=r)
            msgrcpt.rs = 'D'
            msgrcpt.save()

    message = ungettext("%(count)d message deleted successfully",
                        "%(count)d messages deleted successfully",
                        len(mail_id)) % {"count" : len(mail_id)}
    return ajax_response(request, respmsg=message,
                         url=__get_current_url(request))

@login_required
def release(request, mail_id):
    mail_id = check_mail_id(request, mail_id)
    if request.user.group == 'SimpleUsers':
        mb = Mailbox.objects.get(user=request.user)
        print mail_id
        msgrcpts = Msgrcpt.objects.filter(mail__in=mail_id, rid__email=mb.full_address)
        if parameters.get_admin("USER_CAN_RELEASE") == "no":
            print msgrcpts
            msgrcpts.update(rs='p')
            message = ungettext("%(count)d request sent",
                                "%(count)d requests sent",
                                len(mail_id)) % {"count" : len(mail_id)}
            return ajax_response(request, "ok", respmsg=message,
                                 url=__get_current_url(request))
    else:
        msgrcpts = []
        for mid in mail_id:
            r, i = mid.split()
            msgrcpts += [Msgrcpt.objects.get(mail=i, rid__email=r)]

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
                            len(mail_id)) % {"count" : len(mail_id)}
    else:
        message = error
    return ajax_response(request, "ko" if error else "ok", respmsg=message,
                         url=__get_current_url(request))

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
