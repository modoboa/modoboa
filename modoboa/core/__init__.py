from django.utils.translation import ugettext_lazy
from modoboa.lib import parameters


def load_settings():
    from app_settings import GeneralParametersForm, UserSettings
    parameters.register(GeneralParametersForm, ugettext_lazy("General"))
    parameters.register(UserSettings, ugettext_lazy("General"))
