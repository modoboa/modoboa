"""Parsing tools for maillog related files."""

import io
import re
import time

from modoboa.admin import models as admin_models
from modoboa.lib.email_utils import split_mailbox

from . import utils


class MaillogParser:
    """Main parser class for maillog file."""

    def __init__(self, year=None, greylist=False, verbose=False, debug=False):
        """Constructor."""
        self.debug = debug
        self.verbose = verbose

        self.domains = []
        self._load_domain_list()

        self.workdict = {}
        self.lupdates = {}

        self.__year = year
        curtime = time.localtime()
        if not self.__year:
            self.__year = curtime.tm_year
        self.curmonth = curtime.tm_mon

        # set up regular expression
        self._date_expressions = [
            r"(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<hour>\d+):(?P<min>\d+):(?P<sec>\d+)(?P<eol>.*)",  # noqa
            r"(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)T(?P<hour>\d+):(?P<min>\d+):(?P<sec>\d+)\.\d+\+\d+:\d+(?P<eol>.*)"  # noqa
        ]
        self._date_expressions = [
            re.compile(v) for v in self._date_expressions]
        self.date_expr = None
        self._regex = {
            "line": r"\s+([-\w\.]+)\s+(\w+)/?(\w*)[[](\d+)[]]:\s+(.*)",
            "id": r"(\w+): (.*)",
            "reject": r"reject: .*from=<.*>,? to=<[^@]+@([^>]+)>",
            "message-id": r"message-id=<([^>]*)>",
            "from+size": r"from=<([^>]*)>, size=(\d+)",
            "to+status": r"to=<([^>]*)>.*status=(\S+)",
            "orig_to": r"orig_to=<([^>]*)>.*",
        }
        self._regex = {k: re.compile(v) for k, v in self._regex.items()}
        self._srs_regex = {
            "detect_srs": "^SRS[01][+-=]",
            "reverse_srs0": r"^SRS0[+-=]\S+=\S{2}=(\S+)=(\S+)\@\S+$",
            "reverse_srs1": r"^SRS1[+-=]\S+=\S+==\S+=\S{2}=(\S+)=(\S+)\@\S+$"
        }
        self._srs_regex = {
            k: re.compile(v, re.IGNORECASE) for k, v in self._srs_regex.items()
        }

        self.greylist = greylist
        if greylist:
            self._dprint("[settings] greylisting enabled")

    def _load_domain_list(self):
        """Load the list of allowed domains."""
        for dom in admin_models.Domain.objects.all():
            domname = str(dom.name)
            self.domains += [domname]
            # Also add alias domains
            for alias in dom.domainalias_set.all():
                aliasname = str(alias.name)
                self.domains += [aliasname]

    def _dprint(self, msg):
        """Print a debug message if required.

        :param str msg: debug message
        """
        if not self.debug:
            return
        print(msg)

    def year(self, month):
        """Return the appropriate year

        Date used in log files don't always embark the year so we need
        to guess it :p

        This method tries to deal with year changes in a simply
        (ugly?) way: if we currently are in january and the given
        month is different, return the current year -1. Otherwise,
        return the current year.

        Obviously, this method only works for year to year + 1
        changes.

        :param month: the month of the current record beeing parsed
        :return: an integer
        """
        month = (
            time.strptime(month, "%b").tm_mon if not month.isdigit()
            else int(month)
        )
        if self.curmonth == 1 and month != self.curmonth:
            return self.__year - 1
        return self.__year

    def _store_current_date(self, match):
        """Transform and store parsed date."""
        ho = match.group("hour")
        mi = match.group("min")
        se = match.group("sec")
        mo = match.group("month")
        da = match.group("day")
        try:
            ye = match.group("year")
        except IndexError:
            ye = self.year(mo)
        self.cur_t = utils.date_to_timestamp([ye, mo, da, ho, mi, se])

    def _parse_date(self, line):
        """Try to match a date inside :kw:`line` and to convert it to
        a timestamp.

        We try different date format until we find valid one. We then
        store it for future use.

        :param str line: a log entry
        :return: the remaining part of the line or None
        """
        match = None
        if self.date_expr is None:
            for expr in self._date_expressions:
                match = expr.match(line)
                if match is not None:
                    self.date_expr = expr
                    break
        else:
            match = self.date_expr.match(line)
        if match is None:
            return None
        self._store_current_date(match)
        return match.group("eol")

    def is_srs_forward(self, mail_address):
        """ Check if mail address has been mangled by SRS

        Sender Rewriting Scheme (SRS) modifies mail adresses so that they
        always end in a local domain.

        :param str mail_address
        :return a boolean
        """
        return self._srs_regex["detect_srs"].match(mail_address) is not None

    def reverse_srs(self, mail_address):
        """ Try to unwind a mail address rewritten by SRS

        Sender Rewriting Scheme (SRS) modifies mail adresses so that they
        always end in a local domain. Common Postfix implementations of SRS
        rewrite all non-local mail addresss.

        :param str mail_address
        :return a str
        """
        m = self._srs_regex["reverse_srs0"].match(mail_address)
        m = self._srs_regex["reverse_srs1"].match(mail_address) \
            if m is None else m

        if m is not None:
            return "%s@%s" % m.group(2, 1)
        return mail_address

    def new_domain_event(self, domain, name, size=None):
        """Take action about new event for domain."""
        pass

    def new_message_processed(
            self, queue_id, msg_status, from_domain, to_domain, msg_to,
            msg_orig_to):
        """Store new message in local database."""
        pass

    def _parse_postfix(self, log, host, pid, subprog):
        """ Parse a log entry generated by Postfix.

        :param str log: logged message
        :param str host: hostname
        :param str pid: process ID
        :return: True on success
        """
        m = self._regex["id"].match(log)
        if m is None:
            return False

        queue_id, msg = m.groups()

        # Handle rejected mails.
        if queue_id == "NOQUEUE":
            m = self._regex["reject"].match(msg)
            dom = m.group(1) if m is not None else None
            if dom in self.domains:
                condition = (
                    self.greylist and (
                        "Greylisted" in msg or
                        (subprog == "postscreen" and " 450 " in msg))
                )
                self.new_domain_event(
                    dom, "greylist" if condition else "reject")
            return True

        # Message acknowledged.
        m = self._regex["message-id"].search(msg)
        if m is not None:
            self.workdict[queue_id] = {"from": m.group(1), "size": 0}
            return True

        # Message enqueued.
        m = self._regex["from+size"].search(msg)
        if m is not None:
            self.workdict[queue_id] = {
                "from": self.reverse_srs(m.group(1)),
                "size": int(m.group(2))
            }
            return True

        # Message disposition.
        m = self._regex["to+status"].search(msg)
        if m is None:
            return False
        (msg_to, msg_status) = m.groups()
        if queue_id not in self.workdict:
            self._dprint("[parser] inconsistent mail (%s: %s), skipping"
                         % (queue_id, msg_to))
            return True

        # orig_to is optional.
        m = self._regex["orig_to"].search(msg)
        msg_orig_to = m.group(1) if m is not None else None

        # Handle local "from" domains.
        from_domain = split_mailbox(self.workdict[queue_id]["from"])[1]
        if from_domain is not None and from_domain in self.domains:
            self.new_domain_event(
                from_domain, "sent", self.workdict[queue_id]["size"])

        # Handle local "to" domains.
        to_domain = None
        condition = (
            msg_orig_to is not None and
            not self.is_srs_forward(msg_orig_to)
        )
        if condition:
            to_domain = split_mailbox(msg_orig_to)[1]
        if to_domain is None:
            to_domain = split_mailbox(msg_to)[1]

        if msg_status == "sent":
            msg_status = "recv"
        self.new_domain_event(
            to_domain, "recv", self.workdict[queue_id]["size"])

        # Store log entry
        self.new_message_processed(
            queue_id, msg_status, from_domain, to_domain, msg_to, msg_orig_to)

        return True

    def _parse_line(self, line):
        """Parse a single log line.

        :param str line: log line
        """
        line = self._parse_date(line)
        if line is None:
            return
        m = self._regex["line"].match(line)
        if not m:
            return
        host, prog, subprog, pid, log = m.groups()

        try:
            parser = getattr(self, "_parse_{}".format(prog))
            if not parser(log, host, pid, subprog):
                self._dprint("[parser] ignoring %r log: %r" % (prog, log))
        except AttributeError:
            self._dprint(
                "[parser] no log handler for \"%r\": %r".format(prog, log))

    def parse(self, logfile):
        """Process the log file."""
        try:
            fp = io.open(logfile, encoding="utf-8")
        except IOError as errno:
            self._dprint("%s" % errno)
            return

        for line in fp.readlines():
            self._parse_line(line)

        fp.close()
