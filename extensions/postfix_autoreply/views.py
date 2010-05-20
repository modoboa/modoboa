# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.utils import simplejson
from django.contrib.auth.decorators \
    import login_required
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from mailng.lib import _render, _ctx_ok, _ctx_ko
from forms import *
from models import *

@login_required
def autoreply(request):
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
        error = None
        if form.is_valid():
            from mailng import userprefs

            arm = form.save(commit=False)
            arm.mbox = mb
            arm.save()
            request.user.message_set.create(
                message=_("Auto reply message updated successfully.")
                )
            ctx = _ctx_ok(reverse(userprefs.views.index))
        else:
            ctx = _ctx_ko("postfix_autoreply/autoreply.html", {
                    "form" : form, "error" : error
                    })            
        return HttpResponse(simplejson.dumps(ctx), 
                            mimetype="application/json")

    form = ARmessageForm(instance=arm)
    return _render(request, "postfix_autoreply/autoreply.html", {
            "form" : form
            })
