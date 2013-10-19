from django.shortcuts import render
from django.db import transaction
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import (
    login_required, permission_required, user_passes_test
)
from modoboa.lib import events
from modoboa.lib.exceptions import ModoboaException, PermDeniedException
from modoboa.lib.webutils import render_to_json_response
from .models import RelayDomain, Service
from .forms import RelayDomainForm


@login_required
@permission_required("admin.add_relaydomain")
@transaction.commit_on_success
def create(request, tplname="postfix_relay_domains/relaydomain_form.html"):
    commonctx = {"title": _("New relay domain"),
                 "action_label": _("Create"),
                 "action_classes": "submit",
                 "action": reverse(create),
                 "formid": "rdomform"}
    if request.method == 'POST':
        form = RelayDomainForm(request.POST)
        if form.is_valid():
            rdom = form.save(request.user)
            rdom.post_create(request.user)
            return render_to_json_response(
                {"respmsg": _("Relay domain created")}
            )
        return render_to_json_response(form.errors, status=400)
    commonctx['form'] = RelayDomainForm()
    return render(request, tplname, commonctx)


@login_required
@permission_required("admin.change_relaydomain")
def edit(request, rdom_id, tplname='postfix_relay_domains/relaydomain_form.html'):
    rdom = RelayDomain.objects.get(pk=rdom_id)
    if not request.user.can_access(rdom):
        raise PermDeniedException
    if request.method == 'POST':
        form = RelayDomainForm(request.POST, instance=rdom)
        if form.is_valid():
            form.save(request.user)
            events.raiseEvent('RelayDomainModified', rdom)
            return render_to_json_response(
                {'respmsg': _('Relay domain modified')}
            )
        return render_to_json_response(form.errors, status=400)
    ctx = {
        'action': reverse(edit, args=[rdom.id]),
        'formid': 'rdomform',
        'title': rdom.name,
        'action_label': _("Update"),
        'action_classes': "submit",
        'form': RelayDomainForm(instance=rdom)
    }
    return render(request, tplname, ctx)


@login_required
@permission_required("admin.delete_relaydomain")
def delete(request, rdom_id):
    rdom = RelayDomain.objects.get(pk=rdom_id)
    if not request.user.can_access(rdom):
        raise PermDeniedException
    rdom.delete()
    return render_to_json_response({
        'status': 'ok', 'respmsg': _('Relay domain deleted')
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["POST"])
def scan_for_services(request):
    try:
        Service.objects.load_from_master_cf()
    except IOError as e:
        return render_to_json_response([str(e)], status=500)

    return render_to_json_response(
        dict((srv.name, srv.id) for srv in Service.objects.all())
    )
