from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.template import Template, Context
from modoboa.lib import events, parameters


@events.observe("UserMenuDisplay")
def top_menu(target, user):
    if target == "top_menu":
        return [
            {"name": "radicale",
             "label": _("Calendars"),
             "url": reverse('modoboa.extensions.radicale.views.index')}
        ]
    return []


@events.observe('ExtEnabled')
def extension_enabled(extension):
    """ExtEnabled event listener.

    Usefull when *limits* extension is activated after *radicale*.

    :param extension: enabled extension

    """
    if extension.name == 'limits':
        from modoboa.extensions.radicale import (
            init_limits_dependant_features
        )

        init_limits_dependant_features()
