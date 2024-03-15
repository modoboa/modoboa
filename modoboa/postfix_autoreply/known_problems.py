# -*- coding: utf-8 -*-

"""Know problems and associated fixes."""

from __future__ import unicode_literals

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
            _repair.log("Delete {0} (AR does not exist)".format(alr), **options)
            alr.delete()
            deleted += 1
        elif arqs.filter(enabled=False).exists():
            _repair.log("Delete {0} (AR is disabled)".format(alr), **options)
            alr.delete()
            deleted += 1
        if deleted:
            _repair.log("{0} alias recipient(s) deleted".format(deleted), **options)
