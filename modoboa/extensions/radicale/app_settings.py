from django.utils.translation import ugettext_lazy as _
from django import forms
from modoboa.lib.parameters import AdminParametersForm, UserParametersForm
from modoboa.lib.formutils import SeparatorField, YesNoField, InlineRadioSelect


class ParametersForm(AdminParametersForm):
    app = "radicale"
