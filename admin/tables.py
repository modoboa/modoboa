# coding: utf-8
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.lib import tables
from templatetags.admin_extras import *

class DomainsTable(tables.Table):
    tableid = "objects_table"
    idkey = "id"
    styles = "table"

    name = tables.LinkColumn(
        "name", label=ugettext_lazy("Name"), 
        urlpattern="modoboa.admin.views.editdomain",
        title=_("Edit domain"), modal=True, modalcb="domainform_cb"
        )
    domaliases = tables.Column("domainalias_set", 
                               label=ugettext_lazy("Alias(es)"), safe=True)
    actions = tables.ActionColumn("actions", label=ugettext_lazy("Actions"), 
                                  defvalue=domain_actions)

    cols_order = ["name", "domaliases", "actions"]

    def __init__(self, request, doms):
        super(DomainsTable, self).__init__(request)
        self.populate(self._rows_from_model(doms))


    def parse_domainalias_set(self, aliases):
        if not len(aliases.all()):
            return "---"
        res = ""
        for da in aliases.all():
            res += "%s<br/>" % da.name
        return res

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
    styles = "table"
    identity = tables.LinkColumn(
        "identity", label=ugettext_lazy("Email/Username"),
        modal=True,
        urlpattern={"User" : "modoboa.admin.views.editaccount",
                    "Alias" : "modoboa.admin.views.editalias"},
        modalcb={"User" : "editaccount_cb", "Alias" : "aliasform_cb"}
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
