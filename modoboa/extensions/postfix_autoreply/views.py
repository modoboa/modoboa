# coding: utf-8
from datetime import date
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from modoboa.lib.webutils import (
    render_to_json_response, _render_to_string
)
from modoboa.extensions.admin.lib import needs_mailbox
from modoboa.extensions.admin.models import Mailbox
from .forms import ARmessageForm
from .models import ARmessage


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
            arm = form.save(commit=False)
            arm.fromdate = form.cleaned_data["fromdate"]
            arm.untildate = form.cleaned_data["untildate"]
            arm.mbox = mb
            arm.save()
            return render_to_json_response(
                _("Auto reply message updated successfully.")
            )

        return render_to_json_response(
            {"form_errors": form.errors}, status=400
        )

    form = ARmessageForm(instance=arm)
    return render_to_json_response({
        "content": _render_to_string(request, tplname, {"form": form}),
        "onload_cb": "autoreply_cb"
    })
