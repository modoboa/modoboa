# coding: utf-8

"""Core application constants."""

from django.utils.translation import ugettext_lazy

SIMPLEUSERS_ROLE = ("SimpleUsers", ugettext_lazy("Simple user"))
DOMAINADMINS_ROLE = ("DomainAdmins", ugettext_lazy("Domain administrator"))
RESELLERS_ROLE = ("Resellers", ugettext_lazy("Reseller"))
SUPERADMINS_ROLE = ("SuperAdmins", ugettext_lazy("Super administrator"))

ROLES = (
    SIMPLEUSERS_ROLE,
    DOMAINADMINS_ROLE,
    RESELLERS_ROLE,
    SUPERADMINS_ROLE,
)

ADMIN_GROUPS = [
    "SuperAdmins",
    "Resellers",
    "DomainAdmins",
]

LANGUAGES = (
    ("cs", u"čeština"),
    ("de", u"deutsch"),
    ("en", u"english"),
    ("es", u"español"),
    ("fr", u"français"),
    ("it", u"italiano"),
    ("ja_JP", u"日本の"),
    ("nl", u"nederlands"),
    ("pt_PT", u"português"),
    ("pt_BR", u"português (BR)"),
    ("ru", u"русский"),
    ("sv", u"svenska"),
)


# according to https://en.wikipedia.org/wiki/Date_format_by_country
# and https://en.wikipedia.org/wiki/Date_and_time_representation_by_country
DATETIME_FORMATS = {
    "cs": {'SHORT': 'l, H:i', 'LONG': 'd. N Y H:i'},
    "de": {'SHORT': 'l, H:i', 'LONG': 'd. N Y H:i'},
    "en": {'SHORT': 'l, P', 'LONG': 'N j, Y P'},
    "es": {'SHORT': 'l, H:i', 'LONG': 'd. N Y H:i'},
    "fr": {'SHORT': 'l, H:i', 'LONG': 'd. N Y H:i'},
    "it": {'SHORT': 'l, H:i', 'LONG': 'd. N Y H:i'},
    "ja_JP": {'SHORT': 'l, P', 'LONG': 'N j, Y P'},
    "nl": {'SHORT': 'l, H:i', 'LONG': 'd. N Y H:i'},
    "pt_PT": {'SHORT': 'l, H:i', 'LONG': 'd. N Y H:i'},
    "pt_BR": {'SHORT': 'l, H:i', 'LONG': 'd. N Y H:i'},
    "ru": {'SHORT': 'l, H:i', 'LONG': 'd. N Y H:i'},
    "sv": {'SHORT': 'l, H:i', 'LONG': 'd. N Y H:i'},

}

LDAP_GROUP_TYPES = (
    ("posixgroup", "PosixGroup"),
    ("groupofnames", "GroupOfNames"),
)
