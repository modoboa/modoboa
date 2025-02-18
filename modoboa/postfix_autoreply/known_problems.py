"""Know problems and associated fixes."""

from modoboa.admin import models as admin_models
from modoboa.admin.management.commands.subcommands import _repair
from . import models


@_repair.known_problem
def ensure_autoreplies_recipents_are_valids(**options):
    """Sometime autoreply alias exists when ARmessage is not enabled."""
    deleted = 0
    qs = admin_models.AliasRecipient.objects.select_related("alias").filter(
        address__contains="@autoreply."
    )
    for alr in qs:
        address, domain = alr.alias.address.split("@")
        arqs = models.ARmessage.objects.filter(
            mbox__address=address, mbox__domain__name=domain
        )
        if not arqs.exists():
            _repair.log(f"Delete {alr} (AR does not exist)", **options)
            alr.delete()
            deleted += 1
        elif arqs.filter(enabled=False).exists():
            _repair.log(f"Delete {alr} (AR is disabled)", **options)
            alr.delete()
            deleted += 1
        if deleted:
            _repair.log(f"{deleted} alias recipient(s) deleted", **options)
