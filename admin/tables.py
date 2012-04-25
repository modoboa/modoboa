# coding: utf-8
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.lib import tables
from templatetags.admin_extras import *

class DomainsTable(tables.Table):
    tableid = "objects_table"
    idkey = "id"

    name = tables.LinkColumn(
        "name", label=ugettext_lazy("Name"), 
        urlpattern="modoboa.admin.views.editdomain",
        title=_("Edit domain"), modal=True, modalcb="domainform_cb"
        )
    domaliases = tables.Column("domainalias_count", label=ugettext_lazy("Domain aliases"), 
                               width="100px", align="center")
    mboxes = tables.Column("mailbox_count", label=ugettext_lazy("Mailboxes"), 
                           width="100px", align="center")
    mbaliases = tables.Column("mbalias_count", label=ugettext_lazy("Mailbox aliases"),
                              width="100px", align="center")
    quota = tables.Column("quota", label=ugettext_lazy("Quota"), 
                          width="50px", align="center")
    enabled = tables.Column("enabled", label=gender("Enabled", "m"), width="50px",
                            align="center")
    actions = tables.ActionColumn("actions", label=ugettext_lazy("Actions"),  width="70px",
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
    selection = tables.SelectionColumn("selection", width="4%", header=False)
    name = tables.Column("name", label=ugettext_lazy("Name"), width="15%")
    version = tables.Column("version", label=ugettext_lazy("Version"), width="6%")
    descr = tables.Column("description", label=ugettext_lazy("Description"))
    
    cols_order = ["selection", "name", "version", "descr"]

class IdentitiesTable(tables.Table):
    idkey = "id"
    identity = tables.LinkColumn(
        "identity", label=ugettext_lazy("Email/Username"),
        modal=True,
        urlpattern={"User" : "modoboa.admin.views.editaccount",
                    "Alias" : "modoboa.admin.views.editdlist"},
        modalcb={"User" : "editaccount_cb", "Alias" : "dlistform_cb"}
        )
    name_or_rcpt = tables.Column("name_or_rcpt", label=ugettext_lazy("Fullname/Recipient"))
    actions = tables.ActionColumn("actions",  label=ugettext_lazy("Actions"),
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
