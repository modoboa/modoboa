"""Autoreply settings."""

import collections

from django.utils.translation import gettext_lazy as _

AUTOREPLY_PARAMETERS_STRUCT = collections.OrderedDict(
    [
        (
            "general",
            {
                "label": _("General"),
                "params": collections.OrderedDict(
                    [
                        (
                            "tracking_period",
                            {
                                "label": _("Period between two auto-replies"),
                                "help_text": _(
                                    "Number of days to wait before sending a new auto-reply to the same recipient"
                                ),
                            },
                        ),
                        (
                            "default_subject",
                            {
                                "label": _("Default subject"),
                                "help_text": _(
                                    "Default subject used when an auto-reply message is created automatically"
                                ),
                            },
                        ),
                        (
                            "default_content",
                            {
                                "label": _("Default subject"),
                                "help_text": _(
                                    "Default content used when an auto-reply message is created "
                                    "automatically. The '%(name)s' macro will be replaced by the "
                                    "user's full name."
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
    ]
)
