"""SimpleUsers views."""

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
            recipients = form.cleaned_data["dest"]
            if not recipients:
                Alias.objects.filter(
                    address=mb.full_address, internal=False).delete()
                # Make sure internal self-alias is enabled
                Alias.objects.filter(
                    address=mb.full_address, internal=True
                ).update(enabled=True)
            else:
                if al is None:
                    al = Alias.objects.create(
                        address=mb.full_address,
                        domain=mb.domain,
                        enabled=mb.user.is_active
                    )
                    al.post_create(request.user)
                if form.cleaned_data["keepcopies"]:
                    # Make sure internal self-alias is enabled
                    Alias.objects.filter(
                        address=mb.full_address, internal=True
                    ).update(enabled=True)
                else:
                    # Deactivate internal self-alias to avoid storing
                    # local copies...
                    Alias.objects.filter(
                        address=mb.full_address, internal=True
                    ).update(enabled=False)
                al.set_recipients(recipients)
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
