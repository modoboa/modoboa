# coding: utf-8
from django.utils.translation import ugettext_lazy
from django import forms
from modoboa.lib.parameters import AdminParametersForm
from modoboa.lib.formutils import SeparatorField


class ParametersForm(AdminParametersForm):
    app = "stats"

    general_sep = SeparatorField(label=ugettext_lazy("General"))

    logfile = forms.CharField(
        label=ugettext_lazy("Path to the log file"),
        initial="/var/log/mail.log",
        help_text=ugettext_lazy("Path to log file used to collect statistics"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    rrd_rootdir = forms.CharField(
        label=ugettext_lazy("Directory to store RRD files"),
        initial="/tmp/modoboa",
        help_text=ugettext_lazy("Path to directory where RRD files are stored"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
