# coding: utf-8
from django.utils.translation import ugettext as _, ugettext_noop
from modoboa.lib import tables
from templatetags.admin_extras import *

class DomainsTable(tables.Table):
    tableid = "objects_table"
    idkey = "id"

    name = tables.Column("name", label=ugettext_noop("Name"))
    creation = tables.Column("creation", label=ugettext_noop("Created"), width="160px")
    modified = tables.Column("last_modification", label=ugettext_noop("Last modified"), 
                             width="160px")
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
    actions = tables.ActionColumn("actions", label=ugettext_noop("Actions"),  width="50px",
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

    name = tables.Column("name", label=ugettext_noop("Name"))
    target = tables.Column("target", label=ugettext_noop("Targeted domain"))
    creation = tables.Column("creation", label=ugettext_noop("Created"), width="170px")
    modified = tables.Column("last_modification", label=ugettext_noop("Last modified"), 
                             width="170px")
    enabled = tables.Column("enabled", label=gender("Enabled", "m"), width="50px",
                            align="center")
    actions = tables.ActionColumn("actions", label=ugettext_noop("Actions"), 
                                  width="50px", align="center", 
                                  defvalue=domalias_actions)
    
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

    address = tables.Column("full_address", label=ugettext_noop("Address"))
    name = tables.Column("user", label=ugettext_noop("Name"))
    creation = tables.Column("creation", label=ugettext_noop("Created"), 
                             width="160px")
    modified = tables.Column("last_modification", label=ugettext_noop("Last modified"), 
                             width="160px")
    aliases = tables.Column("alias_count", label=ugettext_noop("Aliases"), width="70px",
                            align="center")
    quota = tables.Column("quota", label=ugettext_noop("Quota"), 
                          width="50px", align="center")
    enabled = tables.Column("enabled", label=gender("Enabled", "f"), width="50px",
                            align="center")
    actions = tables.ActionColumn("actions", label=ugettext_noop("Actions"), 
                                  width="70px", align="center", defvalue=mailbox_actions)
    
    cols_order = ["address", "name", "creation", "modified", "aliases",
                  "quota", "enabled", "actions"]

    def __init__(self, request, mailboxes):
        super(MailboxesTable, self).__init__(request)
        self.populate(self._rows_from_model(mailboxes))

    def parse_quota(self, value):
        return "%s %s" % (value, _("MB"))

    def parse_enabled(self, value):
        return _("yes") if value else _("no")

    def parse_name(self, user):
        return "%s %s" % (user.first_name, user.last_name)

class MbaliasesTable(tables.Table):
    tableid = "objects_table"
    idkey = "id"
    
    address = tables.Column("full_address", label=ugettext_noop("Address"))
    targets = tables.Column("targets", label=ugettext_noop("Target(s)"), safe=True)
    creation = tables.Column("creation", label=ugettext_noop("Created"), width="170px")
    modified = tables.Column("last_modification", label=ugettext_noop("Last modified"), 
                             width="170px")
    enabled = tables.Column("enabled", label=gender("Enabled", "m"), width="50px",
                            align="center")
    actions = tables.ActionColumn("actions", label=ugettext_noop("Actions"), width="50px",
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
    name = tables.Column("name", label=ugettext_noop("Name"), width="15%")
    version = tables.Column("version", label=ugettext_noop("Version"), width="6%")
    descr = tables.Column("description", label=ugettext_noop("Description"))
    
    cols_order = ["selection", "name", "version", "descr"]

class SuperAdminsTable(tables.Table):
    idkey = "id"
    selection = tables.SelectionColumn("selection", width="4%", first=True)
    user_name = tables.Column("user_name", label=ugettext_noop("User name"))
    full_name = tables.Column("full_name", label=ugettext_noop("Full name"))
    date_joined = tables.Column("date_joined", label=ugettext_noop("Defined"))
    enabled = tables.Column("enabled", label=gender("Enabled", "m"), width="10%")

    cols_order = ["selection", "user_name", "full_name", "date_joined", "enabled"]
    
class DomainAdminsTable(tables.Table):
    idkey = "id"
    selection = tables.SelectionColumn("selection", width="4%")
    username = tables.Column("username", label=ugettext_noop("User name"))
    first_name = tables.Column("first_name", label=ugettext_noop("First name"))
    last_name = tables.Column("last_name", label=ugettext_noop("Last name"))
    date_joined = tables.Column("date_joined", label=ugettext_noop("Defined"))
    enabled = tables.Column("is_active", label=gender("Enabled", "m"), width="10%")
    actions = tables.ActionColumn("actions", label=ugettext_noop("Actions"),
                                  width="70px", align="center", 
                                  defvalue=domain_admin_actions)

    cols_order = ["selection", "username", "first_name", 
                  "last_name", "date_joined", "enabled", "actions"]
    
    def __init__(self, request, users):
        super(DomainAdminsTable, self).__init__(request)
        self.populate(self._rows_from_model(users))

    def parse_is_active(self, value):
        return _("yes") if value else _("no")
