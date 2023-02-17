"""PDF credentials forms."""

from django import forms
from django.conf import settings
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from django.contrib.sites import models as sites_models

from modoboa.lib import form_utils
from modoboa.parameters import forms as param_forms

from . import constants


class ParametersForm(param_forms.AdminParametersForm):
    """Admin parameters form."""

    app = "pdfcredentials"

    docstore = form_utils.SeparatorField(label=_("Documents storage"))

    storage_dir = forms.CharField(
        label=_("Directory to save documents into"),
        initial="/var/lib/modoboa/pdf_credentials",
        help_text=_("Path to a directory where PDF documents will be saved"),
    )

    security = form_utils.SeparatorField(label=_("Security options"))

    delete_first_dl = form_utils.YesNoField(
        label=_("Delete documents after the first download"),
        initial=True,
        help_text=_(
            "Automatically delete a document just after its first download "
            "from this interface"
        )
    )

    generate_at_creation = form_utils.YesNoField(
        label=_("Generate documents only at account creation"),
        initial=True,
        help_text=_(
            "Generate a new document only when a new account is created. "
            "If set to no, a new document will be created each time a "
            "password is updated."
        )
    )

    customization = form_utils.SeparatorField(label=_("Customization options"))

    title = forms.CharField(
        label=_("Title"),
        initial=_("Personal account information"),
        help_text=_("The document's title")
    )

    webpanel_url = forms.URLField(
        label=_("Web panel url"),
        help_text=_("URL of the Modoboa web panel")
    )

    custom_message = forms.CharField(
        label=_("Custom message"),
        help_text=_(
            "A custom message that will appear at the end of documents"),
        required=False
    )

    include_connection_settings = form_utils.YesNoField(
        label=_("Include mail client connection settings"),
        initial=False,
        help_text=_(
            "Include required SMTP and IMAP connection information to "
            "configure a mail client, a tablet or a phone"
        )
    )

    smtp_server_address = forms.CharField(
        label=_("SMTP server address"),
        help_text=_("Address of the SMTP server (hostname or IP)")
    )

    smtp_server_port = forms.IntegerField(
        label=_("SMTP server port"),
        initial=587,
        help_text=_("Listening port of the SMTP server")
    )

    smtp_connection_security = forms.ChoiceField(
        label=_("SMTP connection security"),
        choices=constants.CONNECTION_SECURITY_MODES,
        initial="starttls",
        help_text=_("Connection security mechanism")
    )

    imap_server_address = forms.CharField(
        label=_("IMAP server address"),
        help_text=_("Address of the IMAP server (hostname or IP)")
    )

    imap_server_port = forms.IntegerField(
        label=_("IMAP server port"),
        initial=143,
        help_text=_("Listening port of the IMAP server")
    )

    imap_connection_security = forms.ChoiceField(
        label=_("IMAP connection security"),
        choices=constants.CONNECTION_SECURITY_MODES,
        initial="starttls",
        help_text=_("Connection security mechanism")
    )

    visibility_rules = {
        "smtp_server_address": "include_connection_settings=True",
        "smtp_server_port": "include_connection_settings=True",
        "smtp_connection_security": "include_connection_settings=True",
        "imap_server_address": "include_connection_settings=True",
        "imap_server_port": "include_connection_settings=True",
        "imap_connection_security": "include_connection_settings=True",
    }

    @cached_property
    def hostname(self):
        """Return local hostname."""
        return sites_models.Site.objects.get_current().domain

    def __init__(self, *args, **kwargs):
        """Set initial values."""
        super(ParametersForm, self).__init__(*args, **kwargs)
        if not self.fields["webpanel_url"].initial:
            url = "https://{}{}".format(self.hostname, settings.LOGIN_URL)
            self.fields["webpanel_url"].initial = url
        if not self.fields["smtp_server_address"].initial:
            self.fields["smtp_server_address"].initial = self.hostname
        if not self.fields["imap_server_address"].initial:
            self.fields["imap_server_address"].initial = self.hostname


def load_settings():
    """Load app settings."""
    from modoboa.parameters import tools as param_tools

    param_tools.registry.add(
        "global", ParametersForm, _("PDF credentials"))