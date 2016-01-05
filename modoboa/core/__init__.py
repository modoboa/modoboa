
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from modoboa.lib import events


PERMISSIONS = {
    "SimpleUsers": []
}


@events.observe("TopNotifications")
def check_for_new_version(request, include_all):
    """
    Check if a new version of Modoboa is available.
    """
    from modoboa.core.utils import check_for_updates

    if not request.user.is_superuser:
        return []
    status, extensions = check_for_updates(request)
    if not status:
        return [{"id": "newversionavailable"}] if include_all else []
    return [{
        "id": "newversionavailable",
        "url": reverse("core:index") + "#info/",
        "text": _("One or more updates are available"),
        "level": "info",
    }]

default_app_config = "modoboa.core.apps.CoreConfig"
