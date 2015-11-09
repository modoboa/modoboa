"""
Relay domains settings definition.
"""

from django import forms
from django.utils.translation import ugettext_lazy

from modoboa.lib import events, parameters
from modoboa.lib.form_utils import SeparatorField


EVENTS = [
    "RelayDomainCreated",
    "RelayDomainDeleted",
    "RelayDomainModified",
    "RelayDomainAliasCreated",
    "RelayDomainAliasDeleted",
    "ExtraRelayDomainForm",
    "FillRelayDomainInstances"
]


class AdminParametersForm(parameters.AdminParametersForm):

    """Admin parameters definition."""

    app = "relaydomains"

    general_sep = SeparatorField(label=ugettext_lazy("General"))

    master_cf_path = forms.CharField(
        label=ugettext_lazy("Postfix's master.cf path"),
        initial="/etc/postfix/master.cf",
        help_text=ugettext_lazy('Path to the master.cf configuration file'),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )


def load_relaydomains_settings():
    """Load application settings."""
    parameters.register(
        AdminParametersForm, ugettext_lazy("Relay domains")
    )
    events.declare(EVENTS)
    from . import general_callbacks
