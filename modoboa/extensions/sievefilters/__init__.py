# coding: utf-8
import sys
from django.utils.translation import ugettext_lazy
from modoboa.lib import events, parameters
from modoboa.core.extensions import ModoExtension, exts_pool


class SieveFilters(ModoExtension):
    name = "sievefilters"
    label = "Sieve filters"
    version = "1.0"
    description = ugettext_lazy("Plugin to easily create server-side filters")
    url = "sfilters"
    available_for_topredirection = True

    def load(self):
        from .app_settings import ParametersForm, UserSettings
        parameters.register(ParametersForm, ugettext_lazy("Sieve filters"))
        parameters.register(UserSettings, ugettext_lazy("Message filters"))
        from modoboa.extensions.sievefilters import general_callbacks
        if 'modoboa.extensions.sievefilters.general_callbacks' in sys.modules:
            reload(general_callbacks)

    def destroy(self):
        events.unregister_extension()
        parameters.unregister()

exts_pool.register_extension(SieveFilters)
