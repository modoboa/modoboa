# coding: utf-8
from django.utils.translation import ugettext_lazy
from modoboa.extensions import ModoExtension, exts_pool
from modoboa.lib import parameters

class UserPreferences(ModoExtension):
    name = "userprefs"
    label = ugettext_lazy("User preferences")
    version = "1.0"
    description = ugettext_lazy("Per-user settings")
    always_active = True

    def load(self):
        from app_settings import UserSettings
        parameters.register(UserSettings, ugettext_lazy("General"))

    def destroy(self):
        parameters.unregister()

exts_pool.register_extension(UserPreferences, show=False)
