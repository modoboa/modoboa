from django.utils.translation import ugettext_lazy
from modoboa.lib import parameters, events


def load_settings():
    from app_settings import GeneralParametersForm, UserSettings
    parameters.register(GeneralParametersForm, ugettext_lazy("General"))
    parameters.register(UserSettings, ugettext_lazy("General"))


@events.observe("ExtDisabled")
def unset_default_topredirection(extension):
    """
    Simple callback to change the default redirection if the
    corresponding extension is being disabled.
    """
    topredirection = parameters.get_admin("DEFAULT_TOP_REDIRECTION")
    if topredirection == extension.name:
        parameters.save_admin("DEFAULT_TOP_REDIRECTION", "userprefs")
