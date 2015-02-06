# coding: utf-8
"""
Amavis quarantine views.
"""
import email

import chardet

from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404
from django.template import Template, Context
from django.utils.translation import ugettext as _, ungettext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from modoboa.lib import parameters
from modoboa.lib.exceptions import BadRequest
from modoboa.lib.paginator import Paginator
from modoboa.lib.webutils import (
    getctx, render_to_json_response, _render_to_string
)
from modoboa.extensions.admin.models import Mailbox, Domain
from modoboa.extensions.amavis.templatetags.amavis_tags import (
    quar_menu, viewm_menu
)
from .lib import (
    selfservice, AMrelease, QuarantineNavigationParameters,
    SpamassassinClient, manual_learning_enabled
)
from .forms import LearningRecipientForm
from .models import Msgrcpt
from .sql_connector import get_connector
from .sql_email import SQLemail


def empty_quarantine():
    """Shortcut to use when no content can be displayed."""
    content = "<div class='alert alert-info'>%s</div>" % _("Empty quarantine")
    ctx = getctx("ok", level=2, listing=content)
    return render_to_json_response(ctx)


def get_listing_pages(request, connector):
    """Return listing pages."""
    paginator = Paginator(
        connector.messages_count(),
        int(parameters.get_user(request.user, "MESSAGES_PER_PAGE"))
    )
    page_id = int(connector.navparams.get("page"))
    page = paginator.getpage(page_id)
    if not page:
        return None
    pages = [page]
    if not page.has_next and page.has_previous and page.items < 40:
        pages = [paginator.getpage(page_id - 1)] + pages
    email_list = []
    for page in pages:
        email_list += connector.fetch(page.id_start, page.id_stop)
    return {"pages": [page.number for page in pages], "rows": email_list}


@login_required
def listing_page(request):
    """Return a listing page."""
    navparams = QuarantineNavigationParameters(request)
    previous_page_id = int(navparams["page"]) if "page" in navparams else None
    navparams.store()

    connector = get_connector(user=request.user, navparams=navparams)
    context = get_listing_pages(request, connector)
    if context is None:
        context = {"length": 0}
        navparams["page"] = previous_page_id
    else:
        context["rows"] = _render_to_string(
            request, "amavis/emails_page.html", {"email_list": context["rows"]}
        )
    return render_to_json_response(context)


@login_required
def _listing(request):
    """Listing initial view.

    Called the first time the listing page is displayed.
    """
    if not request.user.is_superuser and request.user.group != 'SimpleUsers':
        if not Domain.objects.get_for_admin(request.user).count():
            return empty_quarantine()

    navparams = QuarantineNavigationParameters(request)
    navparams.store()

    connector = get_connector(user=request.user, navparams=navparams)
    context = get_listing_pages(request, connector)
    if context is None:
        return empty_quarantine()
    context["listing"] = _render_to_string(
        request, "amavis/email_list.html", {"email_list": context["rows"]}
    )
    del context["rows"]
    if request.session.get('location', 'listing') != 'listing':
        context["menu"] = quar_menu(request.user)
    request.session["location"] = "listingx"
    return render_to_json_response(context)


@login_required
def index(request):
    """Default view."""
    check_learning_rcpt = "false"
    if parameters.get_admin("MANUAL_LEARNING") == "yes":
        if request.user.group != "SimpleUsers":
            user_level_learning = parameters.get_admin(
                "USER_LEVEL_LEARNING") == "yes"
            domain_level_learning = parameters.get_admin(
                "DOMAIN_LEVEL_LEARNING") == "yes"
            if user_level_learning or domain_level_learning:
                check_learning_rcpt = "true"
    return render(request, "amavis/index.html", dict(
        selection="quarantine", check_learning_rcpt=check_learning_rcpt
    ))


def getmailcontent_selfservice(request, mail_id):
    mail = SQLemail(mail_id, mformat="plain", links="0")
    return render(request, "common/viewmail.html", {
        "headers": mail.render_headers(),
        "mailbody": mail.body
    })


@selfservice(getmailcontent_selfservice)
def getmailcontent(request, mail_id):
    mail = SQLemail(mail_id, mformat="plain", links="0")
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
<iframe src="{% url 'amavis:mailcontent_get' mail_id %}" id="mailcontent"></iframe>
""").render(Context(dict(mail_id=mail_id)))

    return render(request, tplname, dict(
        mail_id=mail_id, rcpt=rcpt, secret_id=secret_id, content=content
    ))


@selfservice(viewmail_selfservice)
def viewmail(request, mail_id):
    rcpt = request.GET.get("rcpt", None)
    if rcpt is None:
        raise BadRequest(_("Invalid request"))
    if request.user.email == rcpt:
        get_connector().set_msgrcpt_status(rcpt, mail_id, 'V')
    elif request.user.mailbox_set.count():
        mb = Mailbox.objects.get(user=request.user)
        if rcpt == mb.full_address or rcpt in mb.alias_addresses:
            get_connector().set_msgrcpt_status(rcpt, mail_id, 'V')

    content = Template("""
<iframe src="{{ url }}" id="mailcontent"></iframe>
""").render(Context({"url": reverse("amavis:mailcontent_get", args=[mail_id])}))
    menu = viewm_menu(request.user, mail_id, rcpt)
    ctx = getctx("ok", menu=menu, listing=content)
    request.session['location'] = 'viewmail'
    return render_to_json_response(ctx)


@login_required
def viewheaders(request, mail_id):
    """Display message headers."""
    content = get_connector().get_mail_content(mail_id)
    msg = email.message_from_string(content)
    headers = []
    for name, value in msg.items():
        if value:
            result = chardet.detect(value)
            if result["encoding"] is not None:
                value = value.decode(result["encoding"])
        headers += [(name, value)]
    return render(request, 'amavis/viewheader.html', {
        "headers": headers
    })


def check_mail_id(request, mail_id):
    if type(mail_id) in [str, unicode]:
        if "rcpt" in request.POST:
            mail_id = ["%s %s" % (request.POST["rcpt"], mail_id)]
        else:
            mail_id = [mail_id]
    return mail_id


def get_user_valid_addresses(user):
    """Retrieve all valid addresses of a user."""
    valid_addresses = []
    if user.group == 'SimpleUsers':
        valid_addresses.append(user.email)
        try:
            mb = Mailbox.objects.get(user=user)
        except Mailbox.DoesNotExist:
            pass
        else:
            valid_addresses += mb.alias_addresses
    return valid_addresses


def delete_selfservice(request, mail_id):
    rcpt = request.GET.get("rcpt", None)
    if rcpt is None:
        raise BadRequest(_("Invalid request"))
    try:
        get_connector().set_msgrcpt_status(rcpt, mail_id, 'D')
    except Msgrcpt.DoesNotExist:
        raise BadRequest(_("Invalid request"))
    return render_to_json_response(_("Message deleted"))


@selfservice(delete_selfservice)
def delete(request, mail_id):
    """Delete message selection.

    :param str mail_id: message unique identifier
    """
    mail_id = check_mail_id(request, mail_id)
    connector = get_connector()
    valid_addresses = get_user_valid_addresses(request.user)
    for mid in mail_id:
        r, i = mid.split()
        if valid_addresses and r not in valid_addresses:
            continue
        connector.set_msgrcpt_status(r, i, 'D')
    message = ungettext("%(count)d message deleted successfully",
                        "%(count)d messages deleted successfully",
                        len(mail_id)) % {"count": len(mail_id)}
    return render_to_json_response({
        "message": message,
        "url": QuarantineNavigationParameters(request).back_to_listing()
    })


def release_selfservice(request, mail_id):
    rcpt = request.GET.get("rcpt", None)
    secret_id = request.GET.get("secret_id", None)
    if rcpt is None or secret_id is None:
        raise BadRequest(_("Invalid request"))
    connector = get_connector()
    try:
        msgrcpt = connector.get_recipient_message(rcpt, mail_id)
    except Msgrcpt.DoesNotExist:
        raise BadRequest(_("Invalid request"))
    if secret_id != msgrcpt.mail.secret_id:
        raise BadRequest(_("Invalid request"))
    if parameters.get_admin("USER_CAN_RELEASE") == "no":
        connector.set_msgrcpt_status(rcpt, mail_id, 'p')
        msg = _("Request sent")
    else:
        amr = AMrelease()
        result = amr.sendreq(mail_id, secret_id, rcpt)
        if result:
            connector.set_msgrcpt_status(rcpt, mail_id, 'R')
            msg = _("Message released")
        else:
            raise BadRequest(result)
    return render_to_json_response(msg)


@selfservice(release_selfservice)
def release(request, mail_id):
    """Release message selection.

    :param str mail_id: message unique identifier
    """
    mail_id = check_mail_id(request, mail_id)
    msgrcpts = []
    connector = get_connector()
    valid_addresses = get_user_valid_addresses(request.user)
    for mid in mail_id:
        r, i = mid.split()
        if valid_addresses and r not in valid_addresses:
            continue
        msgrcpts += [connector.get_recipient_message(r, i)]
    if request.user.group == "SimpleUsers" and \
       parameters.get_admin("USER_CAN_RELEASE") == "no":
        for msgrcpt in msgrcpts:
            connector.set_msgrcpt_status(
                msgrcpt.rid.email, msgrcpt.mail.mail_id, 'p'
            )
        message = ungettext("%(count)d request sent",
                            "%(count)d requests sent",
                            len(mail_id)) % {"count": len(mail_id)}
        return render_to_json_response({
            "message": message,
            "url": QuarantineNavigationParameters(request).back_to_listing()
        })

    amr = AMrelease()
    error = None
    for rcpt in msgrcpts:
        result = amr.sendreq(
            rcpt.mail.mail_id, rcpt.mail.secret_id, rcpt.rid.email
        )
        if result:
            connector.set_msgrcpt_status(rcpt.rid.email, rcpt.mail.mail_id, 'R')
        else:
            error = result
            break

    if not error:
        message = ungettext("%(count)d message released successfully",
                            "%(count)d messages released successfully",
                            len(mail_id)) % {"count": len(mail_id)}
    else:
        message = error
    status = 400 if error else 200
    return render_to_json_response({
        "message": message,
        "url": QuarantineNavigationParameters(request).back_to_listing()
    }, status=status)


def mark_messages(request, selection, mtype, recipient_db=None):
    """Mark a selection of messages as spam.

    :param str selection: message unique identifier
    :param str mtype: type of marking (spam or ham)
    """
    if not manual_learning_enabled(request.user):
        return render_to_json_response({"status": "ok"})
    if recipient_db is None:
        recipient_db = (
            "user" if request.user.group == "SimpleUsers" else "global"
        )
    selection = check_mail_id(request, selection)
    connector = get_connector()
    saclient = SpamassassinClient(request.user, recipient_db)
    for item in selection:
        rcpt, mail_id = item.split()
        content = connector.get_mail_content(mail_id)
        result = saclient.learn_spam(rcpt, content) if mtype == "spam" \
            else saclient.learn_ham(rcpt, content)
        if not result:
            break
        connector.set_msgrcpt_status(rcpt, mail_id, mtype[0].upper())
    if saclient.error is None:
        saclient.done()
        message = ungettext("%(count)d message processed successfully",
                            "%(count)d messages processed successfully",
                            len(selection)) % {"count": len(selection)}
    else:
        message = saclient.error
    status = 400 if saclient.error else 200
    return render_to_json_response({
        "message": message, "reload": True
    }, status=status)


@login_required
def learning_recipient(request):
    """A view to select the recipient database of a learning action."""
    if request.method == "POST":
        form = LearningRecipientForm(request.user, request.POST)
        if form.is_valid():
            return mark_messages(
                request,
                form.cleaned_data["selection"].split(","),
                form.cleaned_data["ltype"],
                form.cleaned_data["recipient"]
            )
        return render_to_json_response(
            {"form_errors": form.errors}, status=400
        )
    ltype = request.GET.get("type", None)
    selection = request.GET.get("selection", None)
    if ltype is None or selection is None:
        raise BadRequest
    form = LearningRecipientForm(request.user)
    form.fields["ltype"].initial = ltype
    form.fields["selection"].initial = selection
    return render(request, "common/generic_modal_form.html", {
        "title": _("Select a database"),
        "formid": "learning_recipient_form",
        "action": reverse("amavis:learning_recipient_set"),
        "action_classes": "submit",
        "action_label": _("Validate"),
        "form": form
    })


@login_required
def mark_as_spam(request, mail_id):
    """Mark a single message as spam."""
    return mark_messages(request, mail_id, "spam")


@login_required
def mark_as_ham(request, mail_id):
    """Mark a single message as ham."""
    return mark_messages(request, mail_id, "ham")


@login_required
def process(request):
    """Process a selection of messages.

    The request must specify an action to execute against the
    selection.

    """
    action = request.POST.get("action", None)
    ids = request.POST.get("selection", "")
    ids = ids.split(",")
    if not ids or action is None:
        return HttpResponseRedirect(reverse("amavis:index"))

    if request.POST["action"] == "release":
        return release(request, ids)

    if request.POST["action"] == "delete":
        return delete(request, ids)

    if request.POST["action"] == "mark_as_spam":
        return mark_messages(request, ids, "spam")

    if request.POST["action"] == "mark_as_ham":
        return mark_messages(request, ids, "ham")
