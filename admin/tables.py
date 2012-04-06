# coding: utf-8
from django.utils.translation import ugettext as _, ugettext_noop
from modoboa.lib import tables
from templatetags.admin_extras import *

class DomainsTable(tables.Table):
    tableid = "objects_table"
    idkey = "id"

    name = tables.LinkColumn(
        "name", label=ugettext_noop("Name"), 
        urlpattern="modoboa.admin.views.editdomain",
        title=_("Edit domain"), modal=True, modalcb="domainform_cb"
        )
    domaliases = tables.Column("domainalias_count", label=ugettext_noop("Domain aliases"), 
                               width="100px", align="center")
    mboxes = tables.Column("mailbox_count", label=ugettext_noop("Mailboxes"), 
                           width="100px", align="center")
    mbaliases = tables.Column("mbalias_counter", label=ugettext_noop("Mailbox aliases"),
                              width="100px", align="center")
    quota = tables.Column("quota", label=ugettext_noop("Quota"), 
                          width="50px", align="center")
    enabled = tables.Column("enabled", label=gender("Enabled", "m"), width="50px",
                            align="center")
    actions = tables.ActionColumn("actions", label=ugettext_noop("Actions"),  width="70px",
                                  align="center", defvalue=domain_actions)

    cols_order = ["name", "domaliases", "mboxes", "mbaliases",
                  "quota", "actions"]

    def __init__(self, request, doms):
        super(DomainsTable, self).__init__(request)
        self.populate(self._rows_from_model(doms))

    def parse_quota(self, value):
        return "%s %s" % (value, _("MB"))

    def parse_enabled(self, value):
        return _("yes") if value else _("no")

    def row_class(self, request, domain):
        if not domain.enabled:
            return "muted"
        return ""

class ExtensionsTable(tables.Table):
    idkey = "id"
    selection = tables.SelectionColumn("selection", width="4%", first=True)
    name = tables.Column("name", label=ugettext_noop("Name"), width="15%")
    version = tables.Column("version", label=ugettext_noop("Version"), width="6%")
    descr = tables.Column("description", label=ugettext_noop("Description"))
    
    cols_order = ["selection", "name", "version", "descr"]

class IdentitiesTable(tables.Table):
    idkey = "id"
    identity = tables.Column("identity", label=ugettext_noop("Email/Username"))
    name_or_rcpt = tables.Column("name_or_rcpt", label=ugettext_noop("Fullname/Recipient"))
    actions = tables.ActionColumn("actions",  label=ugettext_noop("Actions"),
                                  width="70px", align="center", 
                                  defvalue=identity_actions)

    cols_order = ["identity", "name_or_rcpt", "actions"]

    def __init__(self, request, identities):
        super(IdentitiesTable, self).__init__(request)
        self.populate(self._rows_from_model(identities, True))

    def row_class(self, request, obj):
        if obj.__class__.__name__ == "User" and not obj.is_active:
            return "muted"
        if not obj.enabled:
            return "muted"
        return ""
