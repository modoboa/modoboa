"""Sieve filters constants."""

from django.utils.translation import gettext_lazy as _


MATCH_TYPE_ALLOF = "allof"
MATCH_TYPE_ANYOF = "anyof"
MATCH_TYPE_ALL = "all"
MATCH_TYPES = [
    (MATCH_TYPE_ALLOF, _("All of the following")),
    (MATCH_TYPE_ANYOF, _("Any of the following")),
    (MATCH_TYPE_ALL, _("All messages")),
]

HEADER_OPERATORS = [
    ("contains", _("contains"), "string"),
    ("notcontains", _("does not contain"), "string"),
    ("is", _("is"), "string"),
    ("isnot", _("is not"), "string"),
]

CONDITION_TEMPLATES = [
    {"name": "Subject", "label": _("Subject"), "operators": HEADER_OPERATORS},
    {"name": "From", "label": _("Sender"), "operators": HEADER_OPERATORS},
    {"name": "To", "label": _("Recipient"), "operators": HEADER_OPERATORS},
    {"name": "Cc", "label": _("Cc"), "operators": HEADER_OPERATORS},
    {
        "name": "size",
        "label": _("Size"),
        "operators": [
            ("over", _("is greater than"), "number"),
            ("under", _("is less than"), "number"),
        ],
    },
]

ACTION_TEMPLATES = [
    {
        "name": "fileinto",
        "label": _("Move message to"),
        "args": [
            {"name": "mailbox", "type": "list", "vloader": "user_mailboxes"},
            {
                "name": "copy",
                "type": "boolean",
                "label": _("Keep local copy"),
                "value": ":copy",
            },
        ],
        "args_order": ["copy", "mailbox"],
    },
    {
        "name": "redirect",
        "label": _("Redirect message to"),
        "args": [
            {"name": "address", "type": "string"},
            {
                "name": "copy",
                "type": "boolean",
                "label": _("Keep local copy"),
                "value": ":copy",
            },
        ],
        "args_order": ["copy", "address"],
    },
    {
        "name": "reject",
        "label": _("Reject message"),
        "args": [{"name": "text", "type": "string"}],
    },
    {"name": "stop", "label": _("Stop processing")},
]
