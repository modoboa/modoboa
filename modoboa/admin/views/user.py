# -*- coding: utf-8 -*-

"""SimpleUsers views."""

from __future__ import unicode_literals

from reversion import revisions as reversion

from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from modoboa.lib.web_utils import render_to_json_response
from ..forms import ForwardForm
from ..lib import needs_mailbox
from ..models import Alias


@login_required
@needs_mailbox()
@reversion.create_revision()
def forward(request, tplname="admin/forward.html"):
    mb = request.user.mailbox
    al = Alias.objects.filter(address=mb.full_address, internal=False).first()
    if request.method == "POST":
        form = ForwardForm(request.POST)
        if form.is_valid():
            if al is None:
                al = Alias.objects.create(
                    address=mb.full_address, domain=mb.domain,
                    enabled=mb.user.is_active)
            recipients = form.cleaned_data["dest"]
            if form.cleaned_data["keepcopies"]:
                recipients.append(mb.full_address)
            al.set_recipients(recipients)
            if len(recipients) == 0:
                al.delete()
            else:
                al.post_create(request.user)
            return render_to_json_response(_("Forward updated"))

        return render_to_json_response(
            {"form_errors": form.errors}, status=400
        )

    form = ForwardForm()
    if al is not None and al.recipients:
        recipients = list(al.recipients)
        if al.aliasrecipient_set.filter(r_mailbox=mb).exists():
            form.fields["keepcopies"].initial = True
            recipients.remove(mb.full_address)
        form.fields["dest"].initial = "\n".join(recipients)
    return render_to_json_response({
        "content": render_to_string(tplname, {"form": form}, request)
    })
