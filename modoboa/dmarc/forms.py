"""Custom forms."""

import collections

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from modoboa.dmarc.api.v2 import serializers
from modoboa.lib import form_utils
from modoboa.parameters import forms as param_forms


class ReportOptionsForm(forms.Form):
    """Report display options."""

    current_year = forms.IntegerField(widget=forms.widgets.HiddenInput)
    current_week = forms.IntegerField()
    query = forms.ChoiceField(choices=[("previous", "Previous"), ("next", "Next")])
    resolve_hostnames = forms.BooleanField(initial=False, required=False)

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super().__init__(*args, **kwargs)
        if not args:
            year, week, day = timezone.now().isocalendar()
            self.fields["current_year"].initial = year
            self.fields["current_week"].initial = week


class ParametersForm(param_forms.AdminParametersForm):
    """Extension settings."""

    app = "dmarc"

    qsettings_sep = form_utils.SeparatorField(label=_("DNS settings"))

    enable_rlookups = form_utils.YesNoField(
        label=_("Enable reverse lookups"),
        initial=False,
        help_text=_("Enable reverse DNS lookups (reports will be longer to display)"),
    )


GLOBAL_PARAMETERS_STRUCT = collections.OrderedDict(
    [
        (
            "dns",
            {
                "label": _("DNS settings"),
                "params": collections.OrderedDict(
                    [
                        (
                            "enable_rlookups",
                            {
                                "label": _("Enable reverse lookups"),
                                "help_text": _(
                                    "Enable reverse DNS lookups (reports will be longer to display)"
                                ),
                            },
                        )
                    ]
                ),
            },
        )
    ]
)


def load_settings():
    """Load app settings."""
    from modoboa.parameters import tools as param_tools

    param_tools.registry.add("global", ParametersForm, _("DMARC"))
    param_tools.registry.add2(
        "global",
        "dmarc",
        _("DMARC"),
        GLOBAL_PARAMETERS_STRUCT,
        serializers.DmarcGlobalParametersSerializer,
        True,
    )
