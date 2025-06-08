"""PDF Credentials forms."""

import collections

from django.utils.translation import gettext_lazy as _


PDF_CREDENTIALS_PARAMETERS_STRUCT = collections.OrderedDict(
    [
        (
            "general",
            {
                "label": _("General"),
                "params": collections.OrderedDict(
                    [
                        (
                            "enabled_pdfcredentials",
                            {
                                "label": _("Enable PDF credentials"),
                                "help_text": _(
                                    "Enabled PDF credentials document generation on account creation."
                                ),
                            },
                        )
                    ]
                ),
            },
        ),
        (
            "docstore",
            {
                "label": _("Documents storage"),
                "params": collections.OrderedDict(
                    [
                        (
                            "storage_dir",
                            {
                                "label": _("Directory to save documents into"),
                                "help_text": _(
                                    "Path to a directory where PDF documents will be saved"
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "security",
            {
                "label": _("Security options"),
                "params": collections.OrderedDict(
                    [
                        (
                            "delete_first_dl",
                            {
                                "label": _("Delete documents after the first download"),
                                "help_text": _(
                                    "Automatically delete a document just after its first download "
                                    "from this interface"
                                ),
                            },
                        ),
                        (
                            "generate_at_creation",
                            {
                                "label": _(
                                    "Generate documents only at account creation"
                                ),
                                "help_text": _(
                                    "Generate a new document only when a new account is created. "
                                    "If set to no, a new document will be created each time a "
                                    "password is updated."
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "customization",
            {
                "label": _("Customization options"),
                "params": collections.OrderedDict(
                    [
                        (
                            "title",
                            {
                                "label": _("Title"),
                                "help_text": _("The document's title"),
                            },
                        ),
                        (
                            "webpanel_url",
                            {
                                "label": _("Web panel url"),
                                "help_text": _("URL of the Modoboa web panel"),
                            },
                        ),
                        (
                            "custom_message",
                            {
                                "label": _("Custom message"),
                                "help_text": _(
                                    "A custom message that will appear at the end of documents"
                                ),
                            },
                        ),
                        (
                            "include_connection_settings",
                            {
                                "label": _("Include mail client connection settings"),
                                "help_text": _(
                                    "Include required SMTP and IMAP connection information to "
                                    "configure a mail client, a tablet or a phone"
                                ),
                            },
                        ),
                        (
                            "smtp_server_address",
                            {
                                "label": _("SMTP server address"),
                                "display": "include_connection_settings=True",
                                "help_text": _(
                                    "Address of the SMTP server (hostname or IP)"
                                ),
                            },
                        ),
                        (
                            "smtp_server_port",
                            {
                                "label": _("SMTP server port"),
                                "display": "include_connection_settings=true",
                                "help_text": _("Listening port of the SMTP server"),
                            },
                        ),
                        (
                            "smtp_connection_security",
                            {
                                "label": _("SMTP connection security"),
                                "display": "include_connection_settings=true",
                                "help_text": _("Connection security mechanism"),
                            },
                        ),
                        (
                            "imap_server_address",
                            {
                                "label": _("IMAP server address"),
                                "display": "include_connection_settings=true",
                                "help_text": _(
                                    "Address of the IMAP server (hostname or IP)"
                                ),
                            },
                        ),
                        (
                            "imap_server_port",
                            {
                                "label": _("IMAP server port"),
                                "display": "include_connection_settings=true",
                                "help_text": _("Listening port of the IMAP server"),
                            },
                        ),
                        (
                            "imap_connection_security",
                            {
                                "label": _("IMAP connection security"),
                                "display": "include_connection_settings=true",
                                "help_text": _("Connection security mechanism"),
                            },
                        ),
                    ]
                ),
            },
        ),
    ]
)
