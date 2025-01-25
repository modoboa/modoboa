"""Default Contacts settings."""

import os

PLUGIN_BASE_DIR = os.path.dirname(__file__)

CONTACTS_STATS_FILE = os.path.join(
    PLUGIN_BASE_DIR, "static/modoboa_contacts/webpack-stats.json"
)


def apply(settings):
    """Modify settings."""
    DEBUG = settings["DEBUG"]
    if "webpack_loader" not in settings["INSTALLED_APPS"]:
        settings["INSTALLED_APPS"] += ("webpack_loader",)
    wpl_config = {
        "CONTACTS": {
            "CACHE": not DEBUG,
            "BUNDLE_DIR_NAME": "modoboa_contacts/",
            "STATS_FILE": CONTACTS_STATS_FILE,
            "IGNORE": [".+\.hot-update.js", ".+\.map"],
        }
    }
    if "WEBPACK_LOADER" in settings:
        settings["WEBPACK_LOADER"].update(wpl_config)
    else:
        settings["WEBPACK_LOADER"] = wpl_config
