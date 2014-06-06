from django.utils.translation import ugettext_lazy
from django import forms
from modoboa.lib.parameters import AdminParametersForm


class ParametersForm(AdminParametersForm):
    app = "radicale"

    rights_file_path = forms.CharField(
        label=ugettext_lazy("Radicale rights file path"),
        initial="/etc/radicale/rights",
        help_text=ugettext_lazy("Path to file that contains rights definition")
    )
