# coding: utf-8

"""
The *limits* extension
----------------------
"""
from django.utils.translation import ugettext_lazy

from modoboa.core.extensions import ModoExtension, exts_pool
from modoboa.core.models import User
from modoboa.lib import events, parameters
from .models import LimitTemplates, LimitsPool, Limit


EVENTS = [
    'GetExtraLimitTemplates'
]


class Limits(ModoExtension):
    name = "limits"
    label = "Limits"
    version = "1.0"
    description = ugettext_lazy(
        "Per administrator resources to limit the number of objects "
        "they can create"
    )

    def load(self):
        from modoboa.extensions.limits.app_settings import ParametersForm
        from modoboa.extensions.limits import controls

        parameters.register(ParametersForm, ugettext_lazy("Limits"))
        events.declare(EVENTS)
        from modoboa.extensions.limits import general_callbacks

    def load_initial_data(self):
        """Create pools for existing accounts."""
        for user in User.objects.filter(groups__name="DomainAdmins"):
            pool, created = LimitsPool.objects.get_or_create(user=user)
            for tpl in LimitTemplates().templates:
                Limit.objects.get_or_create(name=tpl[0], pool=pool, maxvalue=0)

exts_pool.register_extension(Limits)
