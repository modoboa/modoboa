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


LDAP_GROUP_TYPES = (
    ("posixgroup", "PosixGroup"),
    ("groupofnames", "GroupOfNames"),
)
