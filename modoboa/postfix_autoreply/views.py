from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from modoboa.admin.lib import needs_mailbox
from modoboa.admin.models import Mailbox
from modoboa.lib.web_utils import render_to_json_response
from .forms import ARmessageForm
from .models import ARmessage


@login_required
@needs_mailbox()
def autoreply(request, tplname="modoboa_postfix_autoreply/autoreply.html"):
    mb = Mailbox.objects.get(user=request.user.id)
    try:
        arm = ARmessage.objects.get(mbox=mb.id)
    except ARmessage.DoesNotExist:
        arm = None
    if request.method == "POST":
        if arm:
            form = ARmessageForm(mb, request.POST, instance=arm)
        else:
            form = ARmessageForm(mb, request.POST)
        if form.is_valid():
            form.save()
            return render_to_json_response(
                _("Auto reply message updated successfully.")
            )

        return render_to_json_response({"form_errors": form.errors}, status=400)

    form = ARmessageForm(mb, instance=arm)
    return render_to_json_response(
        {
            "content": render_to_string(tplname, {"form": form}, request),
            "onload_cb": "autoreply_cb",
        }
    )
