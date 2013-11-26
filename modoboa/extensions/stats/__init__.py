# coding: utf-8

"""
Graphical statistics about emails traffic using RRDtool

This module provides support to retrieve statistics from postfix log :
sent, received, bounced, rejected

"""
import sys
from django.utils.translation import ugettext_lazy
from modoboa.lib import events, parameters
from modoboa.core.extensions import ModoExtension, exts_pool


class Stats(ModoExtension):
    name = "stats"
    label = "Statistics"
    version = "1.0"
    description = ugettext_lazy(
        "Graphical statistics about emails traffic using RRDtool"
    )
    needs_media = True

    def load(self):
        from modoboa.extensions.stats.app_settings import ParametersForm
        events.declare(["GetGraphSets"])
        parameters.register(
            ParametersForm, ugettext_lazy("Graphical statistics")
        )
        from modoboa.extensions.stats import general_callbacks
        if 'modoboa.extensions.stats.general_callbacks' in sys.modules:
            reload(general_callbacks)

    def destroy(self):
        events.unregister_extension()
        parameters.unregister()

exts_pool.register_extension(Stats)
