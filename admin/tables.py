# coding: utf-8
from django.utils.translation import ugettext as _
from modoboa.lib import tables
from templatetags.admin_extras import *

class DomsTable(tables.Table):
    tableid = "objects_table"
    idkey = "id"

    name = tables.Column("name", label=_("Name"))
    creation = tables.Column("creation", label=_("Created"), width="160px")
    modified = tables.Column("last_modification", label=_("Last modified"), 
                             width="160px")
    domaliases = tables.Column("domainalias_set", label=_("Domain aliases"), 
                               width="100px", align="center")
    mboxes = tables.Column("mailbox_set", label=_("Mailboxes"), 
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
        super(DomsTable, self).__init__(request)
        self.populate(self._rows_from_model(doms))

    def parse_domainalias_set(self, value):
        return len(value.all())

    def parse_mailbox_set(self, value):
        return len(value.all())

    def parse_quota(self, value):
        return "%s %s" % (value, _("MB"))

    def parse_enabled(self, value):
        return _("yes") if value else _("no")

class DomAliasesTable(tables.Table):
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
        super(DomAliasesTable, self).__init__(request)
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
    aliases = tables.Column("alias_set", label=_("Aliases"), width="70px",
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

    def parse_alias_set(self, value):
        return len(value.all())

    def parse_quota(self, value):
        return "%s %s" % (value, _("MB"))

    def parse_enabled(self, value):
        return _("yes") if value else _("no")

class MbAliasesTable(tables.Table):
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
        super(MbAliasesTable, self).__init__(request)
        self.populate(self._rows_from_model(aliases))

    def rowoptions(self, request, alias):
        return "{ui_disabled : '%s'}" % alias.ui_disabled(request.user)

    def parse_enabled(self, value):
        return _("yes") if value else _("no")



