# coding: utf-8
from django.utils.translation import ugettext as _
from modoboa.lib import tables
from templatetags.admin_extras import *

class DomainsTable(tables.Table):
    tableid = "objects_table"
    idkey = "id"

    name = tables.Column("name", label=_("Name"))
    creation = tables.Column("creation", label=_("Created"), width="160px")
    modified = tables.Column("last_modification", label=_("Last modified"), 
                             width="160px")
    domaliases = tables.Column("domainalias_count", label=_("Domain aliases"), 
                               width="100px", align="center")
    mboxes = tables.Column("mailbox_count", label=_("Mailboxes"), 
                           width="100px", align="center")
    mbaliases = tables.Column("mbalias_counter", label=_("Mailbox aliases"),
                              width="100px", align="center")
    quota = tables.Column("quota", label=_("Quota"), width="50px", align="center")
    enabled = tables.Column("enabled", label=_("Enabled"), width="50px",
                            align="center")
    actions = tables.ActionColumn("actions", label=_("Actions"),  width="50px",
                                  align="center", defvalue=domain_actions)

    cols_order = ["name", "creation", "modified", 
                  "domaliases", "mboxes", "mbaliases",
                  "quota", "enabled", "actions"]

    def __init__(self, request, doms):
        super(DomainsTable, self).__init__(request)
        self.populate(self._rows_from_model(doms))

    def parse_quota(self, value):
        return "%s %s" % (value, _("MB"))

    def parse_enabled(self, value):
        return _("yes") if value else _("no")

class DomaliasesTable(tables.Table):
    tableid = "objects_table"
    idkey = "id"

    name = tables.Column("name", label=_("Name"))
    target = tables.Column("target", label=_("Targeted domain"))
    creation = tables.Column("creation", label=_("Created"), width="170px")
    modified = tables.Column("last_modification", label=_("Last modified"), 
                             width="170px")
    enabled = tables.Column("enabled", label=_("Enabled"), width="50px",
                            align="center")
    actions = tables.ActionColumn("actions", label=_("Actions"),  width="50px",
                                  align="center", defvalue=domalias_actions)
    
    cols_order = ["name", "target", "creation",
                  "modified", "enabled", "actions"]

    def __init__(self, request, domaliases):
        super(DomaliasesTable, self).__init__(request)
        self.populate(self._rows_from_model(domaliases))

    def parse_enabled(self, value):
        return _("yes") if value else _("no")

class MailboxesTable(tables.Table):
    tableid = "objects_table"
    idkey = "id"

    address = tables.Column("address", label=_("Address"))
    name = tables.Column("name", label=_("Name"))
    creation = tables.Column("creation", label=_("Created"), width="160px")
    modified = tables.Column("last_modification", label=_("Last modified"), 
                             width="160px")
    aliases = tables.Column("alias_count", label=_("Aliases"), width="70px",
                            align="center")
    quota = tables.Column("quota", label=_("Quota"), width="50px", align="center")
    enabled = tables.Column("enabled", label=gender("Enabled", "f"), width="50px",
                            align="center")
    actions = tables.ActionColumn("actions", label=_("Actions"),  width="70px",
                                  align="center", defvalue=mailbox_actions)
    
    cols_order = ["address", "name", "creation", "modified", "aliases",
                  "quota", "enabled", "actions"]

    def __init__(self, request, mailboxes):
        super(MailboxesTable, self).__init__(request)
        self.populate(self._rows_from_model(mailboxes))

    def parse_quota(self, value):
        return "%s %s" % (value, _("MB"))

    def parse_enabled(self, value):
        return _("yes") if value else _("no")

class MbaliasesTable(tables.Table):
    tableid = "objects_table"
    idkey = "id"
    
    address = tables.Column("full_address", label=_("Address"))
    targets = tables.Column("targets", label=_("Target(s)"), safe=True)
    creation = tables.Column("creation", label=_("Created"), width="170px")
    modified = tables.Column("last_modification", label=_("Last modified"), 
                             width="170px")
    enabled = tables.Column("enabled", label=gender("Enabled", "m"), width="50px",
                            align="center")
    actions = tables.ActionColumn("actions", label=_("Actions"),  width="50px",
                                  align="center", defvalue=mbalias_actions)

    cols_order = ["address", "targets", "creation", "modified", "enabled", "actions"]

    def __init__(self, request, aliases):
        super(MbaliasesTable, self).__init__(request)
        self.populate(self._rows_from_model(aliases))

    def rowoptions(self, request, alias):
        return "{ui_disabled : '%s'}" % alias.ui_disabled(request.user)

    def parse_enabled(self, value):
        return _("yes") if value else _("no")

class ExtensionsTable(tables.Table):
    idkey = "id"
    selection = tables.SelectionColumn("selection", width="4%", first=True)
    name = tables.Column("name", label=_("Name"), width="15%")
    version = tables.Column("version", label=_("Version"), width="6%")
    descr = tables.Column("description", label=_("Description"))
    
    cols_order = ["selection", "name", "version", "descr"]
