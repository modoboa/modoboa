# coding: utf-8
from django.utils.translation import ugettext_lazy
from modoboa.lib import tables


class ExtensionsTable(tables.Table):
    idkey = "id"
    selection = tables.SelectionColumn("selection", width="4%", header=False)
    label = tables.Column("label", label=ugettext_lazy("Name"), width="15%")
    version = tables.Column(
        "version", label=ugettext_lazy("Version"), width="6%"
    )
    descr = tables.Column("description", label=ugettext_lazy("Description"))

    cols_order = ["selection", "label", "version", "descr"]
