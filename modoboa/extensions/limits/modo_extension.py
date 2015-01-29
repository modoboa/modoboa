# coding: utf-8

"""
The *limits* extension
----------------------
"""
from django.utils.translation import ugettext_lazy

from modoboa.core.extensions import ModoExtension, exts_pool
from modoboa.lib import events, parameters


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

exts_pool.register_extension(Limits)
