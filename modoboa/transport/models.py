"""Transport models."""

from __future__ import unicode_literals

from reversion import revisions as reversion

from django.db import models
from django.utils.translation import ugettext_lazy as _

import jsonfield

from modoboa.admin import models as admin_models


class Transport(admin_models.AdminObject):
    """Transport table."""

    pattern = models.CharField(_("pattern"), unique=True, max_length=254)
    service = models.CharField(_("service"), max_length=30)
    next_hop = models.CharField(_("next hop"), max_length=100, blank=True)
    enabled = models.BooleanField("enabled", default=True)

    _settings = jsonfield.JSONField(default={})

    class Meta:
        ordering = ["pattern"]

    def __str__(self):
        return self.pattern


reversion.register(Transport)
