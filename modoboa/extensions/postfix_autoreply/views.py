# coding: utf-8
from datetime import date
from django.http import HttpResponse
from django.utils import simplejson
from django.contrib.auth.decorators \
    import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib.webutils import _render, ajax_simple_response, ajax_response
from modoboa.lib.decorators import needs_mailbox
from forms import *
from models import *

@login_required
@needs_mailbox()
def autoreply(request, tplname="userprefs/section.html"):
    mb = Mailbox.objects.get(user=request.user.id)
    try:
        arm = ARmessage.objects.get(mbox=mb.id)
    except ARmessage.DoesNotExist:
        arm = None
    if request.method == "POST":
        if arm:
            form = ARmessageForm(request.POST, instance=arm)
        else:
            form = ARmessageForm(request.POST)
        if form.is_valid():
            from modoboa import userprefs

            arm = form.save(commit=False)
            arm.untildate = form.cleaned_data["untildate"]
            arm.mbox = mb
            arm.save()
            return ajax_simple_response(dict(
                        status="ok", respmsg=_("Auto reply message updated successfully.")
                        ))

        return ajax_response(request, status="ko", template="userprefs/form.html", form=form)

    ctx = dict(
        title=_("Auto-reply message"),
        subtitle=_("Define an automatic message to send when you are unavailable"),
        action=reverse(autoreply),
        left_selection="autoreply",
        )
    form = ARmessageForm(instance=arm)
    if arm is not None:
        form.fields['untildate'].initial = arm.untildate
    else:
        form.fields['untildate'].initial = date.today()
    ctx.update(form=form)
    return _render(request, "postfix_autoreply/autoreply.html", ctx)
