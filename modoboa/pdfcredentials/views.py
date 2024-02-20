"""modoboa.pdfcredentials views."""

import os

from django.http import HttpResponse
from django.utils.translation import gettext as _

from django.contrib.auth.decorators import login_required, permission_required

from modoboa.core.models import User
from modoboa.lib.exceptions import ModoboaException, PermDeniedException
from modoboa.parameters import tools as param_tools

from .lib import decrypt_file, get_creds_filename


@login_required
@permission_required("core.add_user")
def get_account_credentials(request, accountid):
    """View to download a document."""
    account = User.objects.get(pk=accountid)
    if not request.user.can_access(account):
        raise PermDeniedException()
    fname = get_creds_filename(account)
    if not os.path.exists(fname):
        raise ModoboaException(_("No document available for this user"))
    content = decrypt_file(fname)
    if param_tools.get_global_parameter("delete_first_dl"):
        os.remove(fname)
    resp = HttpResponse(content)
    resp["Content-Type"] = "application/pdf"
    resp["Content-Length"] = len(content)
    resp["Content-Disposition"] = f"attachment; filename={os.path.basename(fname)};"
    return resp
