"""Internal library."""

from django.utils.translation import gettext as _

from modoboa.admin import models as admin_models
from modoboa.lib.exceptions import BadRequest
from modoboa.transport import backends as tr_backends, models as tr_models


def import_relaydomain(user, row, formopts):
    """Specific code for relay domains import"""
    if len(row) != 7:
        raise BadRequest(_("Invalid line"))
    try:
        target_port = int(row[3].strip())
    except ValueError:
        raise BadRequest(_("Invalid port: {}").format(row[3].strip())) from None
    settings = {
        "relay_target_host": row[2].strip(),
        "relay_target_port": target_port,
        "relay_verify_recipients": (
            row[6].strip().lower() in ["true", "1", "yes", "y"]
        ),
    }
    backend = tr_backends.manager.get_backend("relay")
    errors = backend.clean_fields(settings)
    if errors:
        raise BadRequest(
            _("Invalid settings: {}").format(
                ", ".join(fname for fname, error in errors)
            )
        )
    domain = admin_models.Domain(
        name=row[1].strip(),
        type="relaydomain",
        quota=0,
        enabled=(row[5].strip().lower() in ["true", "1", "yes", "y"]),
    )
    domain.save(creator=user)
    transport = tr_models.Transport(
        pattern=domain.name, service="relay", _settings=settings
    )
    backend.serialize(transport)
    transport.save()
