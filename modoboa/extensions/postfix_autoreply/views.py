# coding: utf-8
from datetime import date
from django.http import HttpResponse
from django.template.loader import render_to_string
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
def autoreply(request, tplname="postfix_autoreply/autoreply.html"):
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

        return ajax_simple_response({
                "status" : "ko", 
                "content" : render_to_string(tplname, {"form" : form}),
                "onload_cb" : "autoreply_cb"
                })

    form = ARmessageForm(instance=arm)
    if arm is not None:
        form.fields['untildate'].initial = arm.untildate
    else:
        form.fields['untildate'].initial = date.today()
    return ajax_simple_response({
            "status" : "ok", 
            "content" : render_to_string(tplname, {"form" : form}),
            "onload_cb" : "autoreply_cb"
            })
