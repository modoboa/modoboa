from django.conf import settings
from django.utils.translation import ugettext_lazy

from modoboa.lib import parameters, tables
from modoboa.lib.email_listing import EmailListing
from . import IMAPconnector, imapheader


class WMtable(tables.Table):

    """Webmail listing table."""

    tableid = "emails"
    styles = "table-hover"
    idkey = "imapid"
    drag = tables.ImgColumn(
        "drag", cssclass="draggable left",
        defvalue="%spics/grippy.png" % settings.STATIC_URL,
        header="<input type='checkbox' name='toggleselect' id='toggleselect' />"
    )
    selection = tables.SelectionColumn(
        "selection", safe=True, header=None, sortable=False
    )
    flags = tables.ImgColumn("flags")
    withatts = tables.ImgColumn("withatts")
    subject = tables.Column(
        "subject", label=ugettext_lazy("Subject"), limit=60,
        cssclass="openable"
    )
    from_ = tables.Column(
        "from", label=ugettext_lazy("From"), limit=30,
        cssclass="openable"
    )
    date = tables.Column(
        "date", label=ugettext_lazy("Date"), cssclass="openable"
    )

    cols_order = [
        "drag", "selection", "flags", "from_", "subject", "withatts", "date"
    ]

    def parse(self, header, value):
        if value is None:
            return ""
        try:
            value = getattr(imapheader, "parse_%s" % header)(value)
        except AttributeError:
            pass
        return value


class ImapListing(EmailListing):
    tpl = "webmail/index.html"
    tbltype = WMtable
    deflocation = "INBOX/"
    defcallback = "wm_updatelisting"
    reset_wm_url = False

    def __init__(self, user, password, **kwargs):
        self.user = user
        self.mbc = IMAPconnector(user=user.username, password=password)
        if "pattern" in kwargs and kwargs["pattern"]:
            self.parse_search_parameters(
                kwargs["criteria"], kwargs["pattern"]
            )
        else:
            self.mbc.criterions = []

        super(ImapListing, self).__init__(**kwargs)
        self.extravars["refreshrate"] = \
            int(parameters.get_user(user, "REFRESH_INTERVAL")) * 1000

    def parse_search_parameters(self, criterion, pattern):

        def or_criterion(old, c):
            if old == "":
                return c
            return "OR (%s) (%s)" % (old, c)

        if criterion == u"both":
            criterion = u"from_addr, subject"
        criterions = ""
        if type(pattern) is unicode:
            pattern = pattern.encode("utf-8")
        if type(criterion) is unicode:
            criterion = criterion.encode("utf-8")
        for c in criterion.split(','):
            if c == "from_addr":
                key = "FROM"
            elif c == "subject":
                key = "SUBJECT"
            else:
                continue
            criterions = \
                or_criterion(criterions, '(%s "%s")' % (key, pattern))
        self.mbc.criterions = [criterions]

    @staticmethod
    def computequota(mbc):
        try:
            return int(float(mbc.quota_actual) \
                / float(mbc.quota_limit) * 100)
        except (AttributeError, TypeError):
            return -1

    def getquota(self):
        return ImapListing.computequota(self.mbc)
