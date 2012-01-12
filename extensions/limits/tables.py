# coding: utf-8

from django.utils.translation import ugettext as _, ugettext_noop
from modoboa.lib import tables
from templatetags.limits_tags import reseller_actions

class ResellersTable(tables.Table):
    tableid =  "resellers_table"
    idkey = "id"

    fname = tables.Column("first_name", label=ugettext_noop("First name"))
    lname = tables.Column("last_name", label=ugettext_noop("Last name"))
    username = tables.Column("username", label=ugettext_noop("Username"))
    created = tables.Column("date_joined", label=ugettext_noop("Created on"))
    actions = tables.ActionColumn("actions", label=ugettext_noop("Actions"),
                                  width="50px",
                                  align="center", defvalue=reseller_actions)

    cols_order = ["username", "fname", "lname", "created", "actions"]

    def __init__(self, request, users):
        super(ResellersTable, self).__init__(request)
        self.populate(self._rows_from_model(users))
