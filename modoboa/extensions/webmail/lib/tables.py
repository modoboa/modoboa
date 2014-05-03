from django.conf import settings
from django.utils.translation import ugettext_lazy

from modoboa.lib import tables
from . import imapheader


class WMtable(tables.Table):
    """
    The webmail listing.
    """
    tableid = "emails"
    styles = "table-condensed"
    idkey = "imapid"
    drag = tables.ImgColumn(
        "drag", cssclass="draggable left", width="1%",
        defvalue="%spics/grippy.png" % settings.STATIC_URL,
        header="<input type='checkbox' name='toggleselect' id='toggleselect' />"
    )
    selection = tables.SelectionColumn(
        "selection", safe=True, width='1%', header=None, sortable=False
    )
    flags = tables.ImgColumn("flags", width="3%")
    withatts = tables.ImgColumn("withatts", width="2%")
    subject = tables.Column(
        "subject", label=ugettext_lazy("Subject"), width="50%", limit=60,
        cssclass="openable"
    )
    from_ = tables.Column(
        "from", width="20%", label=ugettext_lazy("From"), limit=30,
        cssclass="openable"
    )
    date = tables.Column(
        "date", width="15%", label=ugettext_lazy("Date"), cssclass="openable"
    )

    cols_order = [
        "drag", "selection", "withatts", "flags", "subject", "from_", "date"
    ]

    def parse(self, header, value):
        if value is None:
            return ""
        try:
            value = getattr(imapheader, "parse_%s" % header)(value)
        except AttributeError:
            pass
        return value
