import reversion
from django.shortcuts import render
from django.db import transaction
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import (
    login_required, permission_required
)
from modoboa.lib import events
from modoboa.lib.exceptions import PermDeniedException
from modoboa.lib.webutils import render_to_json_response
from .models import RelayDomain, Service
from .forms import RelayDomainForm, RelayDomainFormGeneral


@login_required
@permission_required("postfix_relay_domains.add_relaydomain")
@transaction.commit_on_success
@reversion.create_revision()
def create(request, tplname="postfix_relay_domains/new_relaydomain_form.html"):
    events.raiseEvent("CanCreate", request.user, "relay_domains")
    if request.method == 'POST':
        form = RelayDomainFormGeneral(request.POST)
        if form.is_valid():
            rdom = form.save(request.user)
            rdom.post_create(request.user)
            return render_to_json_response(_("Relay domain created"))
        return render_to_json_response(
            {'form_errors': form.errors}, status=400
        )

    ctx = {"title": _("New relay domain"),
           "action_label": _("Create"),
           "action_classes": "submit",
           "action": reverse("postfix_relay_domains:relaydomain_add"),
           "formid": "rdomform",
           "form": RelayDomainFormGeneral()}
    return render(request, tplname, ctx)


@login_required
@permission_required("postfix_relay_domains.change_relaydomain")
@reversion.create_revision()
def edit(request, rdom_id, tplname='common/tabforms.html'):
    rdom = RelayDomain.objects.get(pk=rdom_id)
    if not request.user.can_access(rdom):
        raise PermDeniedException
    instances = {'general': rdom}
    events.raiseEvent("FillRelayDomainInstances", request.user, rdom, instances)
    return RelayDomainForm(request, instances=instances).process()


@login_required
@permission_required("postfix_relay_domains.delete_relaydomain")
def delete(request, rdom_id):
    rdom = RelayDomain.objects.get(pk=rdom_id)
    if not request.user.can_access(rdom):
        raise PermDeniedException
    rdom.delete()
    return render_to_json_response(_('Relay domain deleted'))


@login_required
@permission_required("postfix_relay_domains.add_service")
@require_http_methods(["POST"])
def scan_for_services(request):
    try:
        Service.objects.load_from_master_cf()
    except IOError as e:
        return render_to_json_response([str(e)], status=500)

    return render_to_json_response(
        dict((srv.name, srv.id) for srv in Service.objects.all())
    )
