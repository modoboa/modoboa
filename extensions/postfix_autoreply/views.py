# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.utils import simplejson
from django.contrib.auth.decorators \
    import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib import _render, ajax_response, is_not_localadmin
from forms import *
from models import *

@login_required
@is_not_localadmin('boxerror')
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
        error = None
        if form.is_valid():
            from modoboa import userprefs

            arm = form.save(commit=False)
            arm.untildate = form.cleaned_data["untildate"]
            arm.mbox = mb
            arm.save()
            messages.info(request, _("Auto reply message updated successfully."),
                          fail_silently=True)
            return ajax_response(request, url=reverse(userprefs.views.index))
        return ajax_response(request, status="ko", template=tplname, 
                             form=form, error=error)

    form = ARmessageForm(instance=arm)
    if arm is not None:
        form.fields['untildate'].initial = arm.untildate
    return _render(request, tplname, {
            "form" : form
            })
