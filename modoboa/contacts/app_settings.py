import collections

from django.utils.translation import gettext_lazy


USER_PREFERENCES_STRUCT = collections.OrderedDict(
    [
        (
            "synchronization",
            {
                "label": gettext_lazy("Synchronization"),
                "params": collections.OrderedDict(
                    [
                        (
                            "enable_carddav_sync",
                            {
                                "label": gettext_lazy(
                                    "Synchonize address book using CardDAV"
                                ),
                                "help_text": gettext_lazy(
                                    "Choose to synchronize or not your address book using CardDAV. "
                                    "You will be able to access your contacts from the outside."
                                ),
                            },
                        ),
                        (
                            "sync_frequency",
                            {
                                "label": gettext_lazy("Synchronization frequency"),
                                "help_text": gettext_lazy(
                                    "Interval in seconds between 2 synchronization requests"
                                ),
                            },
                        ),
                    ]
                ),
            },
        )
    ]
)


def load_settings():
    """Load calendars settings."""
    from modoboa.parameters import tools as param_tools
    from modoboa.contacts import serializers

    param_tools.registry.add2(
        "user",
        "contacts",
        gettext_lazy("Contacts"),
        USER_PREFERENCES_STRUCT,
        serializers.UserPreferencesSerializer,
    )
