"""Admin constants."""

from django.utils.translation import ugettext_lazy as _

DNSBL_PROVIDERS = [
    "b.barracudacentral.org",
    "bl.spamcop.net",
    "dnsbl.sorbs.net",
    "ips.backscatterer.org",
    "psbl.surriel.com",
    "sbl.spamhaus.org",
    "spam.dnsbl.sorbs.net",
    "ubl.unsubscore.com",
    "xbl.spamhaus.org",
    "zen.spamhaus.org",
]

# Do not run tests for these domains.
# https://en.wikipedia.org/wiki/Top-level_domain#Reserved_domains
RESERVED_TLD = [
    "example",
    "invalid",
    "localhost",
    "test"
]

DOMAIN_TYPES = [
    ("domain", _("Domain")),
    ("relaydomain", _("Relay domain")),
]

DKIM_KEY_LENGTHS = [
    (1024, "1024"),
    (2048, "2048"),
    (4096, "4096"),
]

ALARM_OPENED = 1
ALARM_CLOSED = 2

ALARM_STATUSES = [
    (ALARM_OPENED, _("Opened")),
    (ALARM_CLOSED, _("Closed")),
]
