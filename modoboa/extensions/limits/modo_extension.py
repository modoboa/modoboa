# coding: utf-8

"""
The *limits* extension
----------------------
"""
from django.utils.translation import ugettext_lazy

from modoboa.core.extensions import ModoExtension, exts_pool
from modoboa.lib import events, parameters
from .models import LimitsPool, Limit


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
        """Complete existing pools with new limits."""
        new_limits = ["relay_domains_limit", "relay_domain_aliases_limit"]
        for pool in LimitsPool.objects.all():
            for lname in new_limits:
                Limit.objects.get_or_create(name=lname, pool=pool, maxvalue=0)

exts_pool.register_extension(Limits)
