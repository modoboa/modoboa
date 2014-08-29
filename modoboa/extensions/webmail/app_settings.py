# coding: utf-8
from django import forms
from django.utils.translation import ugettext_lazy as _
from modoboa.lib.parameters import AdminParametersForm, UserParametersForm
from modoboa.lib.formutils import SeparatorField, YesNoField, InlineRadioSelect


class ParametersForm(AdminParametersForm):
    app = "webmail"

    sep3 = SeparatorField(label=_("General"))

    max_attachment_size = forms.CharField(
        label=_("Maximum attachment size"),
        initial="2048",
        help_text=_("Maximum attachment size in bytes (or KB, MB, GB if specified)")
    )

    sep1 = SeparatorField(label=_("IMAP settings"))

    imap_server = forms.CharField(
        label=_("Server address"),
        initial="127.0.0.1",
        help_text=_("Address of your IMAP server")
    )

    imap_secured = YesNoField(
        label=_("Use a secured connection"),
        initial="no",
        help_text=_("Use a secured connection to access IMAP server")
    )

    imap_port = forms.IntegerField(
        label=_("Server port"),
        initial=143,
        help_text=_("Listening port of your IMAP server")
    )

    sep2 = SeparatorField(label=_("SMTP settings"))

    smtp_server = forms.CharField(
        label=_("Server address"),
        initial="127.0.0.1",
        help_text=_("Address of your SMTP server")
    )

    smtp_secured_mode = forms.ChoiceField(
        label=_("Secured connection mode"),
        choices=[("none", _("None")),
                 ("starttls", "STARTTLS"),
                 ("ssl", "SSL/TLS")],
        initial="none",
        help_text=_("Use a secured connection to access SMTP server"),
        widget=InlineRadioSelect
    )

    smtp_port = forms.IntegerField(
        label=_("Server port"),
        initial=25,
        help_text=_("Listening port of your SMTP server")
    )

    smtp_authentication = YesNoField(
        label=_("Authentication required"),
        initial="no",
        help_text=_("Server needs authentication")
    )


class UserSettings(UserParametersForm):
    app = "webmail"

    sep1 = SeparatorField(label=_("Display"))

    displaymode = forms.ChoiceField(
        initial="plain",
        label=_("Default message display mode"),
        choices=[("html", "html"), ("plain", "text")],
        help_text=_("The default mode used when displaying a message"),
        widget=InlineRadioSelect()
    )

    enable_links = YesNoField(
        initial="no",
        label=_("Enable HTML links display"),
        help_text=_("Enable/Disable HTML links display")
    )

    messages_per_page = forms.IntegerField(
        initial=40,
        label=_("Number of displayed emails per page"),
        help_text=_("Sets the maximum number of messages displayed in a page")
    )

    refresh_interval = forms.IntegerField(
        initial=300,
        label=_("Listing refresh rate"),
        help_text=_("Automatic folder refresh rate (in seconds)")
    )

    mboxes_col_width = forms.IntegerField(
        initial=200,
        label=_("Mailboxes container's width"),
        help_text=_("The width of the mailbox list container")
    )

    sep2 = SeparatorField(label=_("Mailboxes"))

    trash_folder = forms.CharField(
        initial="Trash",
        label=_("Trash folder"),
        help_text=_("Folder where deleted messages go")
    )

    sent_folder = forms.CharField(
        initial="Sent",
        label=_("Sent folder"),
        help_text=_("Folder where copies of sent messages go")
    )

    drafts_folder = forms.CharField(
        initial="Drafts",
        label=_("Drafts folder"),
        help_text=_("Folder where drafts go")
    )

    sep3 = SeparatorField(label=_("Composing messages"))

    editor = forms.ChoiceField(
        initial="plain",
        label=_("Default editor"),
        choices=[("html", "html"), ("plain", "text")],
        help_text=_("The default editor to use when composing a message"),
        widget=InlineRadioSelect()
    )

    signature = forms.CharField(
        initial="",
        label=_("Signature text"),
        help_text=_("User defined email signature"),
        required=False
    )

    visibility_rules = {
        "enable_links": "displaymode=html"
    }

    @staticmethod
    def has_access(user):
        return user.mailbox_set.count() != 0

    def clean_mboxes_col_width(self):
        """Check if the entered value is a positive integer.

        It must also be different from 0.
        """
        if self.cleaned_data['mboxes_col_width'] <= 0:
            raise forms.ValidationError(
                _('Value must be a positive integer (> 0)')
            )
        return self.cleaned_data['mboxes_col_width']
