"""Postfix autoreply forms."""

import collections

from django.utils.translation import gettext_lazy as _

POSTFIX_AUTOREPLY_PARAMETERS_STRUCT = collections.OrderedDict(
    [
        (
            "general",
            {
                "label": _("General"),
                "params": collections.OrderedDict(
                    [
                        (
                            "autoreplies_timeout",
                            {
                                "label": _("Automatic reply timeout"),
                                "help_text": _(
                                    "Timeout in seconds between two auto-replies to the same recipient"
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
