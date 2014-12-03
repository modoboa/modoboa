from django.utils.translation import ugettext_lazy
from django import forms
from modoboa.lib.parameters import AdminParametersForm
from modoboa.lib.formutils import SeparatorField, YesNoField


class ParametersForm(AdminParametersForm):
    app = "radicale"

    server_settings = SeparatorField(
        label=ugettext_lazy("Server settings")
    )

    server_location = forms.CharField(
        label=ugettext_lazy("Server URL"),
        help_text=ugettext_lazy(
            "The URL of your Radicale server. "
            "It will be used to construct calendar URLs."
        ),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    rights_management_sep = SeparatorField(
        label=ugettext_lazy("Rights management"))

    rights_file_path = forms.CharField(
        label=ugettext_lazy("Rights file's path"),
        initial="/etc/radicale/rights",
        help_text=ugettext_lazy(
            "Path to the file that contains rights definition"
        ),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    allow_calendars_administration = YesNoField(
        label=ugettext_lazy("Allow calendars administration"),
        initial="no",
        help_text=ugettext_lazy(
            "Allow domain administrators to manage user calendars "
            "(read and write)"
        )
    )
