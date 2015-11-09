"""Custom views."""

from django.contrib.auth.decorators import (
    login_required, permission_required
)
from django.views.decorators.http import require_http_methods

from modoboa.lib.web_utils import render_to_json_response

from .models import Service


@login_required
@permission_required("relaydomains.add_service")
@require_http_methods(["POST"])
def scan_for_services(request):
    try:
        Service.objects.load_from_master_cf()
    except IOError as e:
        return render_to_json_response([str(e)], status=500)

    return render_to_json_response(
        dict((srv.name, srv.id) for srv in Service.objects.all())
    )
