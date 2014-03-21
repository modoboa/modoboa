"""
Radicale management frontend.

"""
import sys
from django.utils.translation import ugettext_lazy
from modoboa.lib import events, parameters
from modoboa.core.extensions import ModoExtension, exts_pool


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
        pass

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
