#!/usr/bin/env python

import os

import polib


LOCALES = [
    "br",
    "cs",
    "de",
    "el",
    "es",
    "fi",
    "fr",
    "it",
    "ja",
    "nl",
    "pt",
    "pt-br",
    "pl",
    "ru",
    "sv",
    "tr",
    "zh",
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
    "transport",
    "dmarc",
]


def merge_translations():
    for locale in LOCALES:
        target_dir = f"src/locale/{locale}"
        if not os.path.isdir(target_dir):
            os.mkdir(target_dir)
        target = f"{target_dir}/app.po"
        print(f"Opening {target}")
        new_po = polib.pofile(target)
        for module in OLD_TRANSLATION_MODULES:
            prefix = f"../modoboa/{module}" if module else "../modoboa"
            old_file = f"{prefix}/locale/{locale}/LC_MESSAGES/django.po"
            if not os.path.exists(old_file):
                continue
            print(f"Opening {old_file}")
            old_po = polib.pofile(old_file)
            for entry in new_po:
                old_entry = old_po.find(entry.msgid)
                if old_entry:
                    entry.msgstr = old_entry.msgstr
        new_po.save()


if __name__ == "__main__":
    merge_translations()
