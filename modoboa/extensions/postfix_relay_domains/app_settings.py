from django import forms
from django.utils.translation import ugettext_lazy
from modoboa.lib import parameters


class AdminParametersForm(parameters.AdminParametersForm):
    app = "postfix_relay_domains"

    master_cf_path = forms.CharField(
        label=ugettext_lazy("Postfix's master.cf path"),
        initial="/etc/postfix/master.cf",
        help_text=ugettext_lazy('Path to the master.cf configuration file')
    )
