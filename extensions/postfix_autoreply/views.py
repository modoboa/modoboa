# coding: utf-8
from django.http import HttpResponse
from django.utils import simplejson
from django.contrib.auth.decorators \
    import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib.webutils import _render, ajax_response
from modoboa.lib.decorators import needs_mailbox
from forms import *
from models import *

@login_required
@needs_mailbox()
def autoreply(request, tplname="common/generic_modal_form.html"):
    ctx = dict(
        title=_("Auto-reply message"),
        action=reverse(autoreply),
        formid="arform",
        action_label=_("Update"),
        action_classes="submit"
        )
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
            messages.info(request, _("Auto reply message updated successfully."))
            return ajax_response(request, url=reverse(userprefs.views.index))
        ctx.update(form=form, error=error)
        return ajax_response(request, status="ko", template=tplname, **ctx)

    form = ARmessageForm(instance=arm)
    if arm is not None:
        form.fields['untildate'].initial = arm.untildate
    ctx.update(form=form)
    return _render(request, tplname, ctx)
