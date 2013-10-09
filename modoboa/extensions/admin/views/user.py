from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from modoboa.lib.exceptions import ModoboaException
from modoboa.lib.webutils import (
    ajax_response, ajax_simple_response, _render_to_string
)
from modoboa.extensions.admin.lib import needs_mailbox
from modoboa.extensions.admin.exceptions import BadDestination
from modoboa.extensions.admin.models import Alias, Mailbox
from modoboa.extensions.admin.forms import ForwardForm


@login_required
@needs_mailbox()
def forward(request, tplname='admin/forward.html'):
    try:
        mb = request.user.mailbox_set.all()[0]
    except IndexError:
        raise ModoboaException(
            _("You need a mailbox in order to define a forward")
        )
    try:
        al = Alias.objects.get(address=mb.address,
                               domain__name=mb.domain.name)
    except Alias.DoesNotExist:
        al = None
    if request.method == "POST":
        form = ForwardForm(request.POST)
        error = None
        if form.is_valid():
            try:
                if al is None:
                    al = Alias()
                    al.address = mb.address
                    al.domain = mb.domain
                    al.enabled = mb.user.is_active
                intdests = []
                if form.cleaned_data["keepcopies"]:
                    intdests += [mb]
                form.parse_dest()
                al.save(intdests, form.dests)
                if request.user.group != "SimpleUsers":
                    al.post_create(request.user)
                return ajax_response(request, respmsg=_("Forward updated"))
            except BadDestination, e:
                error = str(e)

        return ajax_simple_response(dict(
            status="ko",
            errors=form.errors,
            respmsg=error
        ))

    form = ForwardForm()
    if al is not None:
        form.fields["dest"].initial = al.extmboxes
        try:
            al.mboxes.get(pk=mb.id)
        except Mailbox.DoesNotExist:
            pass
        else:
            form.fields["keepcopies"].initial = True
    return ajax_simple_response({
        "status": "ok",
        "content": _render_to_string(request, tplname, {
            "form": form
        })
    })
