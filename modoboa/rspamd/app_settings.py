"""Modoboa rspamd forms."""

import collections

from django.utils.translation import gettext_lazy as _


RSPAMD_PARAMETERS_STRUCT = collections.OrderedDict(
    [
        (
            "dkim_settings_sep",
            {
                "label": _("DKIM signing settings"),
                "params": collections.OrderedDict(
                    [
                        (
                            "key_map_path",
                            {
                                "label": _("Key map path"),
                                "help_text": _(
                                    "Absolute path of the file which contains "
                                    "paths to DKIM private keys. "
                                    "Must be readable by _rspamd group or user."
                                ),
                            },
                        ),
                        (
                            "selector_map_path",
                            {
                                "label": _("Selector map path"),
                                "help_text": _(
                                    "Absolute path of the file which contains "
                                    "names of DKIM selectors. "
                                    "Must be readable by _rspamd group or user."
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "miscellaneous_sep",
            {
                "label": _("Miscellaneous"),
                "params": collections.OrderedDict(
                    [
                        (
                            "rspamd_dashboard_location",
                            {
                                "label": _("Rspamd dashboard location"),
                                "help_text": _(
                                    "Location of the rspamd dashboard. "
                                    "Can either be a relative URL (eg. '/rspamd') "
                                    "or a full URL (eg. 'https://rspamd.domain.tld/')."
                                    "Only use for guidance on the Super-Admin dashboard."
                                ),
                            },
                        ),
                    ],
                ),
            },
        ),
    ]
)
