import collections

from django.utils.translation import gettext_lazy


GLOBAL_PARAMETERS_STRUCT = collections.OrderedDict(
    [
        (
            "general",
            {
                "label": gettext_lazy("General"),
                "params": collections.OrderedDict(
                    [
                        (
                            "max_attachment_size",
                            {
                                "label": gettext_lazy("Maximum attachment size"),
                                "help_text": gettext_lazy(
                                    "Maximum attachment size in bytes (or KB, MB, GB if specified)"
                                ),
                            },
                        )
                    ]
                ),
            },
        ),
        (
            "imap",
            {
                "label": gettext_lazy("IMAP settings"),
                "params": collections.OrderedDict(
                    [
                        (
                            "imap_server",
                            {
                                "label": gettext_lazy("Server address"),
                                "help_text": gettext_lazy(
                                    "Address of your IMAP server"
                                ),
                            },
                        ),
                        (
                            "imap_secured",
                            {
                                "label": gettext_lazy("Use a secured connection"),
                                "help_text": gettext_lazy(
                                    "Use a secured connection to access IMAP server"
                                ),
                            },
                        ),
                        (
                            "imap_port",
                            {
                                "label": gettext_lazy("Server port"),
                                "help_text": gettext_lazy(
                                    "Listening port of your IMAP server"
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "smtp",
            {
                "label": gettext_lazy("SMTP settings"),
                "params": collections.OrderedDict(
                    [
                        (
                            "smtp_server",
                            {
                                "label": gettext_lazy("Server address"),
                                "help_text": gettext_lazy(
                                    "Address of your SMTP server"
                                ),
                            },
                        ),
                        (
                            "smtp_secured_mode",
                            {
                                "label": gettext_lazy("Secured connection mode"),
                                "help_text": gettext_lazy(
                                    "Use a secured connection to access SMTP server"
                                ),
                            },
                        ),
                        (
                            "smtp_port",
                            {
                                "label": gettext_lazy("Server port"),
                                "help_text": gettext_lazy(
                                    "Listening port of your SMTP server"
                                ),
                            },
                        ),
                        (
                            "smtp_authentication",
                            {
                                "label": gettext_lazy("Authentication required"),
                                "help_text": gettext_lazy(
                                    "Server needs authentication"
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
    ]
)

USER_PREFERENCES_STRUCT = collections.OrderedDict(
    [
        (
            "display",
            {
                "label": gettext_lazy("Display"),
                "params": collections.OrderedDict(
                    [
                        (
                            "displaymode",
                            {
                                "label": gettext_lazy("Default message display mode"),
                                "help_text": gettext_lazy(
                                    "The default mode used when displaying a message"
                                ),
                            },
                        ),
                        (
                            "enable_links",
                            {
                                "label": gettext_lazy("Enable HTML links display"),
                                "display": "displaymode=html",
                                "help_text": gettext_lazy(
                                    "Enable/Disable HTML links display"
                                ),
                            },
                        ),
                        (
                            "messages_per_page",
                            {
                                "label": gettext_lazy(
                                    "Number of displayed emails per page"
                                ),
                                "help_text": gettext_lazy(
                                    "Sets the maximum number of messages displayed in a page"
                                ),
                            },
                        ),
                        (
                            "refresh_interval",
                            {
                                "label": gettext_lazy("Listing refresh rate"),
                                "help_text": gettext_lazy(
                                    "Automatic listing refresh rate (in secconds)"
                                ),
                            },
                        ),
                        (
                            "mboxes_col_width",
                            {
                                "label": gettext_lazy("Folder container's width"),
                                "help_text": gettext_lazy(
                                    "The width of the folder list container"
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "folders",
            {
                "label": gettext_lazy("Folders"),
                "params": collections.OrderedDict(
                    [
                        (
                            "trash_folder",
                            {
                                "label": gettext_lazy("Trash folder"),
                                "help_text": gettext_lazy(
                                    "Folder where deleted messages go"
                                ),
                            },
                        ),
                        (
                            "sent_folder",
                            {
                                "label": gettext_lazy("Sent folder"),
                                "help_text": gettext_lazy(
                                    "Folder where copies of sent messages go"
                                ),
                            },
                        ),
                        (
                            "drafts_folder",
                            {
                                "label": gettext_lazy("Drafts folder"),
                                "help_text": gettext_lazy("Folder where drafts go"),
                            },
                        ),
                        (
                            "junk_folder",
                            {
                                "label": gettext_lazy("Junk folder"),
                                "help_text": gettext_lazy(
                                    "Folder where junk messages should go"
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "composing",
            {
                "label": gettext_lazy("Composing messages"),
                "params": collections.OrderedDict(
                    [
                        (
                            "editor",
                            {
                                "label": gettext_lazy("Default editor"),
                                "help_text": gettext_lazy(
                                    "The default editor to use when composing a message"
                                ),
                            },
                        ),
                        (
                            "signature",
                            {
                                "label": gettext_lazy("Signature text"),
                                "help_text": gettext_lazy(
                                    "User defined email signature"
                                ),
                                "widget": "HTMLField",
                            },
                        ),
                    ]
                ),
            },
        ),
    ]
)


def load_settings():
    """Load webmail settings."""
    from modoboa.parameters import tools as param_tools
    from modoboa.webmail import serializers

    param_tools.registry.add(
        "global",
        "webmail",
        gettext_lazy("Webmail"),
        GLOBAL_PARAMETERS_STRUCT,
        serializers.GlobalParametersSerializer,
    )
    param_tools.registry.add(
        "user",
        "webmail",
        gettext_lazy("Webmail"),
        USER_PREFERENCES_STRUCT,
        serializers.UserPreferencesSerializer,
    )
