# coding: utf-8
from django.utils.translation import ugettext_lazy as _
from django import forms
from modoboa.lib.parameters import AdminParametersForm, UserParametersForm
from modoboa.lib.formutils import SeparatorField, YesNoField, InlineRadioSelect


class ParametersForm(AdminParametersForm):
    app = "amavis"

    qsettings_sep = SeparatorField(label=_("Quarantine settings"))

    max_messages_age = forms.IntegerField(
        label=_("Maximum message age"),
        initial=14,
        help_text=_("Quarantine messages maximum age (in days) before deletion"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    sep1 = SeparatorField(label=_("Messages releasing"))
                          
    released_msgs_cleanup = YesNoField(
        label=_("Remove released messages"),
        initial="no",
        help_text=_("Remove messages marked as released while cleaning up the database")
    )

    am_pdp_mode = forms.ChoiceField(
        label=_("Amavis connection mode"),
        choices=[("inet", "inet"), ("unix", "unix")],
        initial="unix",
        help_text=_("Mode used to access the PDP server"),
        widget=InlineRadioSelect(attrs={"type": "checkbox"})
    )

    am_pdp_host = forms.CharField(
        label=_("PDP server address"),
        initial="localhost",
        help_text=_("PDP server address (if inet mode)"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    am_pdp_port = forms.IntegerField(
        label=_("PDP server port"),
        initial=9998,
        help_text=_("PDP server port (if inet mode)"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    am_pdp_socket = forms.CharField(
        label=_("PDP server socket"),
        initial="/var/amavis/amavisd.sock",
        help_text=_("Path to the PDP server socket (if unix mode)"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    
    check_requests_interval = forms.IntegerField(
        label=_("Check requests interval"),
        initial=30,
        help_text=_("Interval between two release requests checks"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    user_can_release = YesNoField(
        label=_("Allow direct release"),
        initial="no",
        help_text=_("Allow users to directly release their messages")
    )

    self_service = YesNoField(
        label=_("Enable self-service mode"),
        initial="no",
        help_text=_("Activate the 'self-service' mode")
    )

    notifications_sender = forms.EmailField(
        label=_("Notifications sender"),
        initial="notification@modoboa.org",
        help_text=_("The e-mail address used to send notitications"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    visibility_rules = {
        "am_pdp_host": "am_pdp_mode=inet",
        "am_pdp_port": "am_pdp_mode=inet",
        "am_pdp_socket": "am_pdp_mode=unix"
    }


class UserSettings(UserParametersForm):
    app = "amavis"

    dsep = SeparatorField(label=_("Display"))

    messages_per_page = forms.IntegerField(
        initial=40,
        label=_("Number of displayed emails per page"),
        help_text=_("Set the maximum number of messages displayed in a page"),
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
