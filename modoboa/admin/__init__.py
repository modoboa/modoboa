# coding: utf-8

from django import forms
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.lib import parameters, events
from modoboa.lib.formutils import YesNoField, SeparatorField
from modoboa.lib.sysutils import exec_cmd


def enabled_applications():
    """Return the list of currently enabled extensions

    We check if the table exists before trying to fetch activated
    extensions because the admin module is always imported by Django,
    even before the database exists (example: the first ``syncdb``).

    :return: a list
    """
    from modoboa.admin.models import Extension
    from modoboa.lib.dbutils import db_table_exists

    result = [("admin", "admin"), ("userprefs", "userprefs")]
    if db_table_exists("admin_extension"):
        exts = Extension.objects.filter(enabled=True)
        result += [(ext.name, ext.name) for ext in exts]
    return sorted(result, key=lambda e: e[0])


class GeneralParametersForm(parameters.AdminParametersForm):
    app = "admin"

    sep1 = SeparatorField(label=ugettext_lazy("Authentication"))

    authentication_type = forms.ChoiceField(
        label=ugettext_lazy("Authentication type"),
        choices=[('local', ugettext_lazy("Local")),
                 ('ldap', "LDAP")],
        initial="local",
        help_text=ugettext_lazy("The backend used for authentication")
    )

    password_scheme = forms.ChoiceField(
        label=ugettext_lazy("Default password scheme"),
        choices=[("crypt", "crypt"),
                 ("md5", "md5"),
                 ("md5crypt", "md5crypt"),
                 ("sha256", "sha256"),
                 ("plain", "plain")],
        initial="md5crypt",
        help_text=ugettext_lazy("Scheme used to crypt mailbox passwords")
    )

    secret_key = forms.CharField(
        label=ugettext_lazy("Secret key"),
        initial="abcdefghijklmnop",
        help_text=ugettext_lazy("Key used to encrypt/decrypt passwords")
    )

    sep2 = SeparatorField(label=ugettext_lazy("Mailboxes"))

    handle_mailboxes = YesNoField(
        label=ugettext_lazy("Handle mailboxes on filesystem"),
        initial="no",
        help_text=ugettext_lazy("Rename or remove mailboxes on the filesystem when they get renamed or removed within Modoboa")
    )

    mailboxes_owner = forms.CharField(
        label=ugettext_lazy("Mailboxes ower"),
        initial="vmail",
        help_text=ugettext_lazy("The UNIX account who owns mailboxes on the filesystem")
    )

    auto_account_removal = YesNoField(
        label=ugettext_lazy("Automatic account removal"),
        initial="no",
        help_text=ugettext_lazy("When a mailbox is removed, also remove the associated account"),
    )

    sep3 = SeparatorField(label=ugettext_lazy("Miscellaneous"))

    items_per_page = forms.IntegerField(
        label=ugettext_lazy("Items per page"),
        initial=30,
        help_text=ugettext_lazy("Number of displayed items per page")
    )

    default_top_redirection = forms.ChoiceField(
        label=ugettext_lazy("Default top redirection"),
        choices=[],
        initial="admin",
        help_text=ugettext_lazy("The default redirection used when no application is specified")
    )

    def __init__(self, *args, **kwargs):
        super(GeneralParametersForm, self).__init__(*args, **kwargs)
        self.fields["default_top_redirection"].choices = enabled_applications()
        hide_fields = False
        try:
            code, version = exec_cmd("dovecot --version")
        except OSError, e:
            hide_fields = True
        else:
            if code or not version.strip().startswith("2"):
                hide_fields = True
        if hide_fields:
            del self.fields["handle_mailboxes"]
            del self.fields["mailboxes_owner"]

    # Visibility rules
    def visibility_mailboxes_owner(self):
        return "handle_mailboxes=yes"


parameters.register(GeneralParametersForm, ugettext_lazy("General"))


@events.observe("ExtDisabled")
def unset_default_topredirection(extension):
    """
    Simple callback to change the default redirection if the
    corresponding extension is being disabled.
    """
    topredirection = parameters.get_admin("DEFAULT_TOP_REDIRECTION")
    if topredirection == extension.name:
        parameters.save_admin("DEFAULT_TOP_REDIRECTION", "userprefs")
