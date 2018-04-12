"""Default admin app settings."""

import os

PLUGIN_BASE_DIR = os.path.dirname(__file__)

ADMIN_STATS_FILES = {
    "dev": os.path.join(
        PLUGIN_BASE_DIR, "../frontend/webpack-stats.json"),
    "prod": os.path.join(
        PLUGIN_BASE_DIR, "static/admin/webpack-stats.json")
}


def apply(settings):
    """Modify settings."""
    DEBUG = settings['DEBUG']
    if "webpack_loader" not in settings["INSTALLED_APPS"]:
        settings["INSTALLED_APPS"] += ("webpack_loader", )
    settings["WEBPACK_LOADER"] = {
        "ADMIN": {
            "CACHE": not DEBUG,
            "BUNDLE_DIR_NAME": "admin/",
            "STATS_FILE": ADMIN_STATS_FILES.get("dev" if DEBUG else "prod"),
            "IGNORE": [".+\.hot-update.js", ".+\.map"]
        }
    }
