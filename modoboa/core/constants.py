# coding: utf-8

"""Core application constants."""

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
