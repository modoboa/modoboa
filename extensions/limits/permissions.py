# coding: utf-8

from django.utils.translation import ugettext as _, ugettext_noop
from modoboa.lib import events

@events.observe("GetExtraRoles")
def get_extra_roles(user):
    if user.is_superuser:
        return [("Resellers", _("Reseller")),]
    return []
