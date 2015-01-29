# coding: utf-8
"""Declare and register the webmail extension."""

from django.utils.translation import ugettext_lazy

from modoboa.core.extensions import ModoExtension, exts_pool
from modoboa.lib import parameters


class Webmail(ModoExtension):
    name = "webmail"
    label = "Webmail"
    version = "1.0"
    description = ugettext_lazy("Simple IMAP webmail")
    needs_media = True
    available_for_topredirection = True

    def load(self):
        from .app_settings import ParametersForm, UserSettings

        parameters.register(ParametersForm, "Webmail")
        parameters.register(UserSettings, "Webmail")
        from modoboa.extensions.webmail import general_callbacks

exts_pool.register_extension(Webmail)
