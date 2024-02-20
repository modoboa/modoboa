"""Modoboa stats forms."""

import rrdtool

from pkg_resources import parse_version

from django.conf import settings
from django.utils.translation import gettext_lazy
from django import forms

from modoboa.lib import form_utils
from modoboa.parameters import forms as param_forms


class ParametersForm(param_forms.AdminParametersForm):
    """Stats global parameters."""

    app = "maillog"

    general_sep = form_utils.SeparatorField(label=gettext_lazy("General"))

    logfile = forms.CharField(
        label=gettext_lazy("Path to the log file"),
        initial="/var/log/mail.log",
        help_text=gettext_lazy("Path to log file used to collect statistics"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    rrd_rootdir = forms.CharField(
        label=gettext_lazy("Directory to store RRD files"),
        initial="/tmp/modoboa",
        help_text=gettext_lazy("Path to directory where RRD files are stored"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    greylist = form_utils.YesNoField(
        label=gettext_lazy("Show greylisted messages"),
        initial=False,
        help_text=gettext_lazy(
            "Differentiate between hard and soft rejects (greylisting)"
        ),
    )

    def __init__(self, *args, **kwargs):
        """Check RRDtool version."""
        super().__init__(*args, **kwargs)
        rrd_version = parse_version(rrdtool.lib_version())
        required_version = parse_version("1.6.0")
        test_mode = getattr(settings, "RRDTOOL_TEST_MODE", False)
        if rrd_version < required_version and not test_mode:
            del self.fields["greylist"]
