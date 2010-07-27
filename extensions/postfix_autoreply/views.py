# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.utils import simplejson
from django.contrib.auth.decorators \
    import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib import _render, _ctx_ok, _ctx_ko, is_not_localadmin
from forms import *
from models import *

@login_required
@is_not_localadmin('boxerror')
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
            from modoboa import userprefs

            arm = form.save(commit=False)
            arm.mbox = mb
            arm.save()
            messages.info(request, _("Auto reply message updated successfully."),
                          fail_silently=True)
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
