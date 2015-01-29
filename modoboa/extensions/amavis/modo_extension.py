# coding: utf-8
"""
Amavis management frontend.

Provides:

* SQL quarantine management
* Per-domain settings

"""
import sys

from django.utils.translation import ugettext_lazy

from modoboa.core.extensions import ModoExtension, exts_pool
from modoboa.lib import parameters


class Amavis(ModoExtension):
    name = "amavis"
    label = "Amavis frontend"
    version = "1.0"
    description = ugettext_lazy("Simple amavis management frontend")
    url = "quarantine"
    available_for_topredirection = True

    def load(self):
        from .app_settings import ParametersForm, UserSettings

        parameters.register(ParametersForm, "Amavis")
        parameters.register(UserSettings, ugettext_lazy("Quarantine"))
        from modoboa.extensions.amavis import general_callbacks

exts_pool.register_extension(Amavis)
