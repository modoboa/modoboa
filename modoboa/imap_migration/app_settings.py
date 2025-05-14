"""IMAP migration forms."""

import collections

from django.utils.translation import gettext_lazy as _


IMAP_MIGRATION_PARAMETERS_STRUCT = collections.OrderedDict(
    [
        (
            "general",
            {
                "label": _("General"),
                "params": collections.OrderedDict(
                    [
                        (
                            "enabled_imapmigration",
                            {
                                "label": _("Enable IMAP Migration"),
                                "help_text": _("Enable IMAP Migration."),
                            },
                        )
                    ]
                ),
            },
        ),
        (
            "offlineimap",
            {
                "label": _("OfflineIMAP"),
                "params": collections.OrderedDict(
                    [
                        (
                            "max_sync_accounts",
                            {
                                "label": _("Concurrent sync jobs"),
                                "help_text": _(
                                    "The maximum number of concurrent synchronization jobs"
                                ),
                            },
                        )
                    ]
                ),
            },
        ),
        (
            "offlineimapfilter",
            {
                "label": _("OfflineIMAP Filter"),
                "params": collections.OrderedDict(
                    [
                        (
                            "create_folders",
                            {
                                "label": _("Create Folders"),
                                "help_text": _(
                                    "Allow Creation of missing folders during sync"
                                ),
                            },
                        ),
                        (
                            "folder_filter_exclude",
                            {
                                "label": _("Folder Filter Exclusions"),
                                "help_text": _(
                                    "Use a regular expression to explicitly include folders in sync. "
                                    "Example: ^Trash$|Del"
                                ),
                            },
                        ),
                        (
                            "folder_filter_include",
                            {
                                "label": _("Folder Filter Inclusions"),
                                "help_text": _(
                                    "A comma seperated list of folders to explicitly include in sync "
                                    "even if filtered by the Folder Filter Exclusions. Example: "
                                    "debian.user, debian.personal "
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
    ]
)
