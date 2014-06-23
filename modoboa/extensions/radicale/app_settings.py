from django.utils.translation import ugettext_lazy
from django import forms
from modoboa.lib.parameters import AdminParametersForm
from modoboa.lib.formutils import SeparatorField


class ParametersForm(AdminParametersForm):
    app = "radicale"

    rights_management_sep = SeparatorField(
        label=ugettext_lazy("Rights management"))

    rights_file_path = forms.CharField(
        label=ugettext_lazy("Radicale rights file path"),
        initial="/etc/radicale/rights",
        help_text=ugettext_lazy("Path to file that contains rights definition")
    )

    allow_calendars_administration = forms.BooleanField(
        label=ugettext_lazy("Allow calendars administration"),
        initial=False,
        help_text=ugettext_lazy(
            "Allow domain administrators to manage user calendars (read an write)"
        )
    )
