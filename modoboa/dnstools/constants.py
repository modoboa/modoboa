"""App related constants."""

import re


DNS_RECORD_TYPES = [
    ("spf", "SPF"),
    ("dkim", "DKIM"),
    ("dmarc", "DMARC"),
    ("autoconfig", "Autoconfig"),
    ("autodiscover", "Autodiscover"),
]

SPF_MECHANISMS = ["ip4", "ip6", "a", "mx", "ptr", "exists", "include"]

DMARC_URI_REGEX = re.compile(r"^mailto:(.+)(!\w+)?")

DMARC_TAGS = {
    "adkim": {"values": ["r", "s"]},
    "aspf": {"values": ["r", "s"]},
    "fo": {"values": ["0", "1", "d", "s"]},
    "p": {"values": ["none", "quarantine", "reject"]},
    "pct": {"type": "int", "min_value": 0, "max_value": 100},
    "rf": {"type": "list", "values": ["afrf"]},
    "ri": {"type": "int"},
    "rua": {"type": "list", "regex": DMARC_URI_REGEX},
    "ruf": {"type": "list", "regex": DMARC_URI_REGEX},
    "sp": {"values": ["none", "quarantine", "reject"]}
}
