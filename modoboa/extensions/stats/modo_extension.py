# coding: utf-8

"""
Graphical statistics about emails traffic using RRDtool

This module provides support to retrieve statistics from postfix log :
sent, received, bounced, rejected

"""
import sys

from django.utils.translation import ugettext_lazy

from modoboa.core.extensions import ModoExtension, exts_pool
from modoboa.lib import events, parameters


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

exts_pool.register_extension(Stats)
