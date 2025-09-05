"""SQL connector module."""

import datetime

from django.db.models import Q

from modoboa.admin.models import Domain
from modoboa.lib.email_utils import decode

from .lib import cleanup_email_address, make_query_args
from .models import Maddr, Msgrcpt, Quarantine
from .utils import ConvertFrom, fix_utf8_encoding, smart_bytes, smart_str


def reverse_domain_names(domains):
    """Return a list of reversed domain names."""
    return [".".join(reversed(domain.split("."))) for domain in domains]


class SQLconnector:
    """This class handles all database operations."""

    ORDER_TRANSLATION_TABLE = {
        "type": "content",
        "score": "bspam_level",
        "datetime": "mail__time_num",
        "subject": "mail__subject",
        "from_address": "mail__from_addr",
        "to_address": "rid__email",
    }

    QUARANTINE_FIELDS = [
        "content",
        "bspam_level",
        "rs",
        "rid__email",
        "mail__from_addr",
        "mail__subject",
        "mail__mail_id",
        "mail__time_num",
    ]

    def __init__(self, user=None, ordering: str | None = None) -> None:
        """Constructor."""
        self.user = user
        self.messages = None
        self.ordering = ordering

        self._messages_count = None
        self._annotations = {}

    def _exec(self, query, args):
        """Execute a raw SQL query.

        :param string query: query to execute
        :param list args: a list of arguments to replace in :kw:`query`
        """
        from django.db import connections, transaction

        with transaction.atomic():
            cursor = connections["amavis"].cursor()
            cursor.execute(query, args)

    def _apply_msgrcpt_simpleuser_filter(self, flt):
        """Apply specific filter for simple users."""
        if "str_email" not in self._annotations:
            self._annotations["str_email"] = ConvertFrom("rid__email")

        rcpts = [self.user.email]
        if hasattr(self.user, "mailbox"):
            rcpts += self.user.mailbox.alias_addresses

        query_rcpts = []
        for rcpt in rcpts:
            query_rcpts += make_query_args(rcpt, exact_extension=False, wildcard=".*")

        re = f"({'|'.join(query_rcpts)})"
        return flt & Q(str_email__regex=re)

    def _apply_msgrcpt_filters(self, flt):
        """Apply filters based on user's role."""
        if self.user.role == "SimpleUsers":
            flt = self._apply_msgrcpt_simpleuser_filter(flt)
        elif not self.user.is_superuser:
            doms = Domain.objects.get_for_admin(self.user).values_list(
                "name", flat=True
            )
            flt &= Q(rid__domain__in=reverse_domain_names(doms))
        return flt

    def _get_quarantine_content(self, request):
        """Fetch quarantine content.

        Filters: rs, rid, content
        """
        flt = (
            Q(rs__in=[" ", "V", "R", "p", "S", "H"])
            if request.GET.get("viewrequests", "0") != "1"
            else Q(rs="p")
        )
        flt = self._apply_msgrcpt_filters(flt)
        search = request.GET.get("search")
        if search:
            criteria = request.GET.get("criteria", "both")
            if criteria == "both":
                criteria = "from_addr,subject,to"
            search_flt = None
            for crit in criteria.split(","):
                if crit == "from_addr":
                    nfilter = Q(mail__from_addr__icontains=search)
                elif crit == "subject":
                    nfilter = Q(mail__subject__icontains=search)
                elif crit == "to":
                    if "str_email" not in self._annotations:
                        self._annotations["str_email"] = ConvertFrom("rid__email")
                    nfilter = Q(str_email__icontains=search)
                else:
                    continue
                search_flt = nfilter if search_flt is None else search_flt | nfilter
            if search_flt:
                flt &= search_flt

        msgtype = request.GET.get("msgtype")
        if msgtype is not None:
            flt &= Q(content=msgtype)

        flt &= Q(mail__in=Quarantine.objects.filter(chunk_ind=1).values("mail_id"))

        return (
            Msgrcpt.objects.annotate(**self._annotations)
            .select_related("mail", "rid")
            .filter(flt)
        )

    def messages_count(self, request) -> int:
        """
        Return the total number of messages living in the quarantine.

        We also store the built queryset for a later use.
        """
        if self.user is None:
            return None
        if self._messages_count is None:
            self.messages = self._get_quarantine_content(request)
            self.messages = self.messages.values(*self.QUARANTINE_FIELDS)

            order = self.ordering
            if order is not None:
                sign = ""
                if order[0] == "-":
                    sign = "-"
                    order = order[1:]
                order = self.ORDER_TRANSLATION_TABLE.get(order)
                if order:
                    self.messages = self.messages.order_by(sign + order)

            self._messages_count = len(self.messages)

        return self._messages_count

    def fetch(self, start=None, stop=None):
        """Fetch a range of messages from the internal cache."""
        emails = []
        for qm in self.messages[start - 1 : stop]:
            if qm["rs"] == "D":
                continue
            m = {
                "from_address": cleanup_email_address(
                    fix_utf8_encoding(qm["mail__from_addr"])
                ),
                "to_address": smart_str(qm["rid__email"]),
                "subject": fix_utf8_encoding(qm["mail__subject"]),
                "mailid": smart_str(qm["mail__mail_id"]),
                "datetime": datetime.datetime.fromtimestamp(qm["mail__time_num"]),
                "type": qm["content"],
                "score": qm["bspam_level"],
                "status": qm["rs"],
            }
            if qm["rs"] in ["", " "]:
                m["style"] = "unseen"
            elif qm["rs"] == "p":
                m["style"] = "pending"
            emails.append(m)
        return emails

    def get_recipient_message(self, address, mailid):
        """Retrieve a message for a given recipient."""
        assert isinstance(address, str), "address should be of type str"

        return Msgrcpt.objects.annotate(str_email=ConvertFrom("rid__email")).get(
            mail=mailid.encode("ascii"), str_email=address
        )

    def set_msgrcpt_status(self, address, mailid: str, status):
        """Change the status (rs field) of a message recipient.

        :param string status: status
        """
        assert isinstance(address, str), "address should be of type str"
        addr = Maddr.objects.annotate(str_email=ConvertFrom("email")).get(
            str_email=address
        )
        self._exec(
            "UPDATE msgrcpt SET rs=%s WHERE mail_id=%s AND rid=%s",
            [status, mailid.encode("ascii"), addr.id],
        )

    def get_domains_pending_requests(self, domains):
        """Retrieve pending release requests for a list of domains."""
        return Msgrcpt.objects.filter(
            rs="p", rid__domain__in=reverse_domain_names(domains)
        )

    def get_pending_requests(self):
        """Return the number of requests currently pending."""
        rq = Q(rs="p")
        if not self.user.is_superuser:
            doms = Domain.objects.get_for_admin(self.user)
            if not doms.exists():
                return 0
            doms_q = Q(
                rid__domain__in=reverse_domain_names(
                    doms.values_list("name", flat=True)
                )
            )
            rq &= doms_q
        return Msgrcpt.objects.filter(rq).count()

    def get_mail_content(self, mailid) -> str:
        """Retrieve the content of a message."""
        content_bytes = smart_bytes("").join(
            [
                smart_bytes(qmail.mail_text)
                for qmail in Quarantine.objects.filter(mail=mailid)
            ]
        )
        content = decode(
            content_bytes, "utf-8", append_to_error=f"; mail_id={smart_str(mailid)}"
        )
        return content
