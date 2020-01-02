"""Internal library."""

from django.utils.translation import ugettext as _

from modoboa.admin import models as admin_models
from modoboa.lib.exceptions import BadRequest
from modoboa.transport import backends as tr_backends, models as tr_models


def import_relaydomain(user, row, formopts):
    """Specific code for relay domains import"""
    if len(row) != 7:
        raise BadRequest(_("Invalid line"))
    domain = admin_models.Domain(
        name=row[1].strip(), type="relaydomain", quota=0,
        enabled=(row[5].strip().lower() in ["true", "1", "yes", "y"])
    )
    domain.save(creator=user)
    settings = {
        "relay_target_host": row[2].strip(),
        "relay_target_port": row[3].strip(),
        "relay_verify_recipients": (
            row[6].strip().lower() in ["true", "1", "yes", "y"])
    }
    transport = tr_models.Transport(
        pattern=domain.name, service="relay", _settings=settings)
    tr_backends.manager.get_backend("relay").serialize(transport)
    transport.save()
