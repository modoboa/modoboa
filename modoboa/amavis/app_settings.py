import collections

from django.utils.translation import gettext_lazy


GLOBAL_PARAMETERS_STRUCT = collections.OrderedDict(
    [
        (
            "amavis",
            {
                "label": gettext_lazy("Amavis settings"),
                "params": collections.OrderedDict(
                    [
                        (
                            "localpart_is_case_sensitive",
                            {
                                "label": gettext_lazy("Localpart is case sensitive"),
                                "help_text": gettext_lazy(
                                    "Value should match amavisd.conf variable "
                                    "$localpart_is_case_sensitive"
                                ),
                            },
                        ),
                        (
                            "recipient_delimiter",
                            {
                                "label": gettext_lazy("Recipient delimiter"),
                                "help_text": gettext_lazy(
                                    "Value should match amavisd.conf variable "
                                    "$recipient_delimiter"
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "quarantine",
            {
                "label": gettext_lazy("Quarantine settings"),
                "params": collections.OrderedDict(
                    [
                        (
                            "max_messages_age",
                            {
                                "label": gettext_lazy("Maximum message age"),
                                "help_text": gettext_lazy(
                                    "Quarantine messages maximum age (in days) before deletion"
                                ),
                            },
                        )
                    ]
                ),
            },
        ),
        (
            "releasing",
            {
                "label": gettext_lazy("Message releasing"),
                "params": collections.OrderedDict(
                    [
                        (
                            "released_msgs_cleanup",
                            {
                                "label": gettext_lazy("Remove released messages"),
                                "help_text": gettext_lazy(
                                    "Remove messages marked as released while cleaning up "
                                    "the database"
                                ),
                            },
                        ),
                        (
                            "am_pdp_mode",
                            {
                                "label": gettext_lazy("Amavis connection mode"),
                                "help_text": gettext_lazy(
                                    "Mode used to access the PDP server"
                                ),
                            },
                        ),
                        (
                            "am_pdp_host",
                            {
                                "label": gettext_lazy("PDP server address"),
                                "help_text": gettext_lazy(
                                    "PDP server address (if inet mode)"
                                ),
                                "display": "am_pdp_mode=inet",
                            },
                        ),
                        (
                            "am_pdp_port",
                            {
                                "label": gettext_lazy("PDP server port"),
                                "help_text": gettext_lazy(
                                    "PDP server port (if inet mode)"
                                ),
                                "display": "am_pdp_mode=inet",
                            },
                        ),
                        (
                            "am_pdp_socket",
                            {
                                "label": gettext_lazy("PDP server socket"),
                                "help_text": gettext_lazy(
                                    "Path to the PDP server socket (if unix mode)"
                                ),
                                "display": "am_pdp_mode=unix",
                            },
                        ),
                        (
                            "user_can_release",
                            {
                                "label": gettext_lazy("Allow direct release"),
                                "help_text": gettext_lazy(
                                    "Allow users to directly release their messages"
                                ),
                            },
                        ),
                        (
                            "self_service",
                            {
                                "label": gettext_lazy("Enable self-service mode"),
                                "help_text": gettext_lazy(
                                    "Activate the 'self-service' mode"
                                ),
                            },
                        ),
                        (
                            "notifications_sender",
                            {
                                "label": gettext_lazy("Notifications sender"),
                                "help_text": gettext_lazy(
                                    "The e-mail address used to send notitications"
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "learning",
            {
                "label": gettext_lazy("Manual learning"),
                "params": collections.OrderedDict(
                    [
                        (
                            "manual_learning",
                            {
                                "label": gettext_lazy("Enable manual learning"),
                                "help_text": gettext_lazy(
                                    "Allow super administrators to manually train Spamassassin"
                                ),
                            },
                        ),
                        (
                            "sa_is_local",
                            {
                                "label": gettext_lazy("Is Spamassassin local?"),
                                "help_text": gettext_lazy(
                                    "Tell if Spamassassin is running on the same server than modoboa"
                                ),
                                "display": "manual_learning=true",
                            },
                        ),
                        (
                            "default_user",
                            {
                                "label": gettext_lazy("Default user"),
                                "help_text": gettext_lazy(
                                    "Name of the user owning the default bayesian database"
                                ),
                                "display": "manual_learning=true",
                            },
                        ),
                        (
                            "spamd_address",
                            {
                                "label": gettext_lazy("Spamd address"),
                                "help_text": gettext_lazy(
                                    "The IP address where spamd can be reached"
                                ),
                                "display": "sa_is_local=false",
                            },
                        ),
                        (
                            "spamd_port",
                            {
                                "label": gettext_lazy("Spamd port"),
                                "help_text": gettext_lazy(
                                    "The TCP port spamd is listening on"
                                ),
                                "display": "sa_is_local=false",
                            },
                        ),
                        (
                            "domain_level_learning",
                            {
                                "label": gettext_lazy(
                                    "Enable per-domain manual learning"
                                ),
                                "help_text": gettext_lazy(
                                    "Allow domain administrators to train Spamassassin "
                                    "(within dedicated per-domain databases)"
                                ),
                                "display": "manual_learning=true",
                            },
                        ),
                        (
                            "user_level_learning",
                            {
                                "label": gettext_lazy(
                                    "Enable per-user manual learning"
                                ),
                                "help_text": gettext_lazy(
                                    "Allow simple users to personally train Spamassassin "
                                    "(within a dedicated database)"
                                ),
                                "display": "manual_learning=true",
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
                            "messages_per_page",
                            {
                                "label": gettext_lazy(
                                    "Number of displayed emails per page"
                                ),
                                "help_text": gettext_lazy(
                                    "Set the maximum number of messages displayed in a page"
                                ),
                            },
                        )
                    ]
                ),
            },
        )
    ]
)


def load_settings():
    """Load amavis settings."""
    from modoboa.parameters import tools as param_tools
    from modoboa.amavis import serializers

    param_tools.registry.add(
        "global",
        "amavis",
        gettext_lazy("Amavis"),
        GLOBAL_PARAMETERS_STRUCT,
        serializers.GlobalParametersSerializer,
    )
    param_tools.registry.add(
        "user",
        "amavis",
        gettext_lazy("Amavis"),
        USER_PREFERENCES_STRUCT,
        serializers.UserPreferencesSerializer,
    )
