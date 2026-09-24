import collections

from django.utils.translation import gettext_lazy


GLOBAL_PARAMETERS_STRUCT = collections.OrderedDict(
    [
        (
            "server",
            {
                "label": gettext_lazy("Server settings"),
                "params": collections.OrderedDict(
                    [
                        (
                            "server_location",
                            {
                                "label": gettext_lazy("Server URL"),
                                "help_text": gettext_lazy(
                                    "The URL of your Radicale server. "
                                    "It will be used to construct calendar URLs."
                                ),
                            },
                        )
                    ]
                ),
            },
        ),
        (
            "rights",
            {
                "label": gettext_lazy("Rights management"),
                "params": collections.OrderedDict(
                    [
                        (
                            "rights_file_path",
                            {
                                "label": gettext_lazy("Rights file's path"),
                                "help_text": gettext_lazy(
                                    "Path to the file that contains rights definition"
                                ),
                            },
                        ),
                        (
                            "allow_calendars_administration",
                            {
                                "label": gettext_lazy("Allow calendars administration"),
                                "help_text": gettext_lazy(
                                    "Allow domain administrators to manage user calendars "
                                    "(read and write)"
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "misc",
            {
                "label": gettext_lazy("Miscellaneous"),
                "params": collections.OrderedDict(
                    [
                        (
                            "max_ics_file_size",
                            {
                                "label": gettext_lazy("Maximum size of ICS files"),
                                "help_text": gettext_lazy(
                                    "Maximum size in bytes of imported ICS files "
                                    "(or KB, MB, GB if specified)"
                                ),
                            },
                        )
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
                            "working_hours_start",
                            {
                                "label": gettext_lazy("Start of working hours"),
                                "help_text": gettext_lazy(
                                    "Hours outside working hours are greyed out "
                                    "and the calendar scrolls to this hour by default"
                                ),
                            },
                        ),
                        (
                            "working_hours_end",
                            {
                                "label": gettext_lazy("End of working hours"),
                                "help_text": gettext_lazy(
                                    "Hours outside working hours are greyed out"
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
    from modoboa.calendars import serializers

    param_tools.registry.add(
        "global",
        "calendars",
        gettext_lazy("Calendars"),
        GLOBAL_PARAMETERS_STRUCT,
        serializers.GlobalParametersSerializer,
    )
    param_tools.registry.add(
        "user",
        "calendars",
        gettext_lazy("Calendars"),
        USER_PREFERENCES_STRUCT,
        serializers.UserPreferencesSerializer,
    )
