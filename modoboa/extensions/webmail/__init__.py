# coding: utf-8
import sys
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse
from modoboa.lib import events, parameters
from modoboa.core.extensions import ModoExtension, exts_pool


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
        if 'modoboa.extensions.webmail.general_callbacks' in sys.modules:
            reload(general_callbacks)

    def destroy(self):
        events.unregister_extension()
        parameters.unregister()

exts_pool.register_extension(Webmail)
