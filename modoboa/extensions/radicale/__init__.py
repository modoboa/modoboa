"""
Radicale management frontend.

"""
import sys
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy
from modoboa.lib import events, parameters
from modoboa.lib.permissions import add_permissions_to_group
from modoboa.core.extensions import ModoExtension, exts_pool


def init_limits_dependant_features():
    """Custom initialization if the limits extension activated.

    We mainly define extra permissions.
    """
    add_permissions_to_group(
        "Resellers", [("radicale", "add_usercalendar"),
                      ("radicale", "change_usercalendar"),
                      ("radicale", "delete_usercalendar"),
                      ("radicale", "add_sharedcalendar"),
                      ("radicale", "change_sharedcalendar"),
                      ("radicale", "delete_sharedcalendar")]
    )


class Radicale(ModoExtension):
    """
    """
    name = "radicale"
    label = ugettext_lazy("Radicale management frontend")
    version = "1.0"
    description = ugettext_lazy(
        "Management frontend for Radicale, a simple calendar and contact server."
    )

    def init(self):
        """Plugin initialization.
        """
        add_permissions_to_group(
            "DomainAdmins", [("radicale", "add_usercalendar"),
                             ("radicale", "change_usercalendar"),
                             ("radicale", "delete_usercalendar"),
                             ("radicale", "add_sharedcalendar"),
                             ("radicale", "change_sharedcalendar"),
                             ("radicale", "delete_sharedcalendar")]
        )
        if exts_pool.is_extension_enabled('limits'):
            init_limits_dependant_features()

    def load(self):
        """Plugin loading.
        """
        from .app_settings import ParametersForm

        parameters.register(ParametersForm, "Radicale")
        from modoboa.extensions.radicale import general_callbacks
        if 'modoboa.extensions.radicale.general_callbacks' in sys.modules:
            reload(general_callbacks)

    def destroy(self):
        """Plugin unloading.
        """
        events.unregister_extension()
        parameters.unregister()

exts_pool.register_extension(Radicale)
