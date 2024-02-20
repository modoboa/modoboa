"""IMAP migration forms."""

import collections

from django import forms
from django.utils.translation import gettext_lazy as _

from modoboa.lib import form_utils
from modoboa.parameters import forms as param_forms


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


class ParametersForm(param_forms.AdminParametersForm):
    """IMAP migration settings."""

    app = "imap_migration"

    sep1 = form_utils.SeparatorField(label=_("General"))

    enabled_imapmigration = form_utils.YesNoField(
        label=_("Enable IMAP Migration"),
        initial=True,
        help_text=_("Enable IMAP Migration."),
    )

    sep2 = form_utils.SeparatorField(label=_("OfflineIMAP settings"))

    max_sync_accounts = forms.IntegerField(
        label=_("Concurrent sync jobs"),
        initial=1,
        help_text=_("The maximum number of concurrent synchronization jobs"),
    )

    sep3 = form_utils.SeparatorField(label=_("OfflineIMAP Filter settings"))

    create_folders = form_utils.YesNoField(
        label=_("Create Folders"),
        initial=True,
        help_text=_("Allow Creation of missing folders during sync"),
    )

    folder_filter_exclude = forms.CharField(
        required=False,
        label=_("Folder Filter Exclusions"),
        initial="",
        help_text=_(
            "Use a regular expression to explicitly include folders in sync. "
            "Example: ^Trash$|Del"
        ),
    )

    folder_filter_include = forms.CharField(
        required=False,
        label=_("Folder Filter Inclusions"),
        initial="",
        help_text=_(
            "A comma seperated list of folders to explicitly include in sync "
            "even if filtered by the Folder Filter Exclusions. Example: "
            "debian.user, debian.personal "
        ),
    )
