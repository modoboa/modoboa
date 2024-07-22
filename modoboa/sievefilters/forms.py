"""Custom forms."""

from django import forms
from django.utils.translation import gettext_lazy

from modoboa.lib import form_utils
from modoboa.parameters import forms as param_forms


class ParametersForm(param_forms.AdminParametersForm):
    app = "sievefilters"

    sep1 = form_utils.SeparatorField(label=gettext_lazy("ManageSieve settings"))

    server = forms.CharField(
        label=gettext_lazy("Server address"),
        initial="127.0.0.1",
        help_text=gettext_lazy("Address of your MANAGESIEVE server"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    port = forms.IntegerField(
        label=gettext_lazy("Server port"),
        initial=4190,
        help_text=gettext_lazy("Listening port of your MANAGESIEVE server"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    starttls = form_utils.YesNoField(
        label=gettext_lazy("Connect using STARTTLS"),
        initial=False,
        help_text=gettext_lazy("Use the STARTTLS extension"),
    )

    sep2 = form_utils.SeparatorField(label=gettext_lazy("IMAP settings"))

    imap_server = forms.CharField(
        label=gettext_lazy("Server address"),
        initial="127.0.0.1",
        help_text=gettext_lazy("Address of your IMAP server"),
    )

    imap_secured = form_utils.YesNoField(
        label=gettext_lazy("Use a secured connection"),
        initial=False,
        help_text=gettext_lazy("Use a secured connection to access IMAP server"),
    )

    imap_port = forms.IntegerField(
        label=gettext_lazy("Server port"),
        initial=143,
        help_text=gettext_lazy("Listening port of your IMAP server"),
    )


class UserSettings(param_forms.UserParametersForm):
    app = "sievefilters"

    sep1 = form_utils.SeparatorField(label=gettext_lazy("General"))

    editor_mode = forms.ChoiceField(
        initial="gui",
        label=gettext_lazy("Editor mode"),
        choices=[("raw", "raw"), ("gui", "simplified")],
        help_text=gettext_lazy("Select the mode you want the editor to work in"),
        widget=form_utils.HorizontalRadioSelect(),
    )

    sep2 = form_utils.SeparatorField(label=gettext_lazy("Mailboxes"))

    trash_folder = forms.CharField(
        initial="Trash",
        label=gettext_lazy("Trash folder"),
        help_text=gettext_lazy("Folder where deleted messages go"),
    )

    sent_folder = forms.CharField(
        initial="Sent",
        label=gettext_lazy("Sent folder"),
        help_text=gettext_lazy("Folder where copies of sent messages go"),
    )

    drafts_folder = forms.CharField(
        initial="Drafts",
        label=gettext_lazy("Drafts folder"),
        help_text=gettext_lazy("Folder where drafts go"),
    )

    @staticmethod
    def has_access(**kwargs):
        return hasattr(kwargs.get("user"), "mailbox")
