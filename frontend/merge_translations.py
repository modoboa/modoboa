#!/usr/bin/env python

import polib


LOCALES = [
    "fr",
]

OLD_TRANSLATION_MODULES = [
    "",
    "admin",
    "dnstools",
    "ldapsync",
    "limits",
    "maillog",
    "policyd",
    "relaydomains",
    "transport"
]


def merge_translations():
    for locale in LOCALES:
        new_po = polib.pofile(f"locale/{locale}/LC_MESSAGES/app.po")
        for module in OLD_TRANSLATION_MODULES:
            prefix = f"../modoboa/{module}" if module else "../modoboa"
            old_po = polib.pofile(f"{prefix}/locale/{locale}/LC_MESSAGES/django.po")
            for entry in new_po:
                old_entry = old_po.find(entry.msgid)
                if old_entry:
                    entry.msgstr = old_entry.msgstr
        new_po.save()


if __name__ == "__main__":
    merge_translations()
