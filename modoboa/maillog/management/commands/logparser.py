# coding: utf-8

"""
Postfix log parser.

This scripts parses a log file produced by postfix (or using the same
format). It looks for predefined events and build statistics about
their occurence rate.

At the, somes default graphics are generated using the grapher module.
(see grapher.py)

Predefined events are:
 * Per domain sent/received messages,
 * Per domain received bad messages (bounced, reject for now),
 * Per domain sent/received traffics size,
 * Global consolidation of all previous events.

"""

from datetime import datetime
import io
import os
import re
import sys
import time

import rrdtool

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from modoboa.admin.models import Domain
from modoboa.parameters import tools as param_tools
from modoboa.lib.email_utils import split_mailbox

from ... import lib
from ... import models


rrdstep = 60
xpoints = 540
points_per_sample = 3
variables = ["sent", "recv", "bounced", "reject", "spam", "virus",
             "size_sent", "size_recv"]


class LogParser:

    def __init__(self, options, workdir, year=None, greylist=False):
        """Constructor."""
        self.logfile = options["logfile"]
        self.debug = options["debug"]
        self.verbose = options["verbose"]
        try:
            self.f = io.open(self.logfile, encoding="utf-8")
        except IOError as errno:
            self._dprint("%s" % errno)
            sys.exit(1)
        self.workdir = workdir
        self.__year = year
        self.cfs = ["AVERAGE", "MAX"]

        curtime = time.localtime()
        if not self.__year:
            self.__year = curtime.tm_year
        self.curmonth = curtime.tm_mon

        self.data = {"global": {}}
        self.domains = []
        self._load_domain_list()

        self.workdict = {}
        self.lupdates = {}

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
            "amavis": r"(?P<result>INFECTED|SPAM|SPAMMY) .* <[^>]+> -> <[^@]+@(?P<domain>[^>]+)>.*",  # noqa
            "rmilter_line": r"<(?P<hash>[0-9a-f]{10})>; (?P<line>.*)",
            "rmilter_msg_done": r"msg done: queue_id: <(?P<queue_id>[^>]+)>; message id: <(?P<message_id>[^>]+)>.*; from: <(?P<from>[^>]+)>; rcpt: <(?P<rcpt>[^>]+)>.*; spam scan: (?P<action>[^;]+); virus scan:",  # noqa
            "rmilter_spam": r"mlfi_eom: (rejecting spam|add spam header to message according to spamd action)",  # noqa
            "rmilter_virus": r"mlfi_eom:.* virus found",
            "rmilter_greylist": (
                r"GREYLIST\([0-9]+\.[0-9]{2}\)\[greylisted[^\]]*\]")
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
            variables.insert(4, "greylist")
            self._dprint("[settings] greylisting enabled")

        self._prev_se = -1
        self._prev_mi = -1
        self._prev_ho = -1
        self.cur_t = 0

    def _load_domain_list(self):
        """Load the list of allowed domains."""
        for dom in Domain.objects.all():
            domname = str(dom.name)
            self.domains += [domname]
            self.data[domname] = {}

            # Also add alias domains
            for alias in dom.domainalias_set.all():
                aliasname = str(alias.name)
                self.domains += [aliasname]
                self.data[aliasname] = {}

    def _dprint(self, msg):
        """Print a debug message if required.

        :param str msg: debug message
        """
        if not self.debug:
            return
        print(msg)

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
        ho = match.group("hour")
        mi = match.group("min")
        se = match.group("sec")
        mo = match.group("month")
        da = match.group("day")
        try:
            ye = match.group("year")
        except IndexError:
            ye = self.year(mo)
        # Keep original timestamp
        self.orig_ts = lib.date_to_timestamp([ye, mo, da, ho, mi, se])

        # Now get the current period (based on rrdstep)
        se = int(int(se) / rrdstep)  # rrd step is one-minute => se = 0
        if self._prev_se != se or self._prev_mi != mi or self._prev_ho != ho:
            self.cur_t = lib.date_to_timestamp([ye, mo, da, ho, mi, se])
            self.cur_t = self.cur_t - self.cur_t % rrdstep
            self._prev_mi = mi
            self._prev_ho = ho
            self._prev_se = se
        return match.group("eol")

    def init_rrd(self, fname, m):
        """init_rrd.

        Set-up Data Sources (DS)
        Set-up Round Robin Archives (RRA):
        - day,week,month and year archives
        - 2 types : AVERAGE and MAX

        parameter : start time
        return    : last epoch recorded
        """
        ds_type = "ABSOLUTE"
        rows = xpoints / points_per_sample
        realrows = int(rows * 1.1)    # ensure that the full range is covered
        day_steps = int(3600 * 24 / (rrdstep * rows))
        week_steps = day_steps * 7
        month_steps = week_steps * 5
        year_steps = month_steps * 12

        # Set up data sources for our RRD
        params = []
        for v in variables:
            params += ["DS:%s:%s:%s:0:U" % (v, ds_type, rrdstep * 2)]

        # Set up RRD to archive data
        for cf in ["AVERAGE", "MAX"]:
            for step in [day_steps, week_steps, month_steps, year_steps]:
                params += ["RRA:%s:0.5:%s:%s" % (cf, step, realrows)]

        # With those setup, we can now created the RRD
        rrdtool.create(str(fname),
                       "--start", str(m),
                       "--step", str(rrdstep),
                       *params)
        return m

    def add_datasource_to_rrd(self, fname, dsname):
        """Add a new data source to an exisitng file.

        Add missing Data Sources (DS) to existing Round Robin Archive (RRA):
        See init_rrd for details.
        """
        ds_def = "DS:%s:ABSOLUTE:%s:0:U" % (dsname, rrdstep * 2)
        rrdtool.tune(fname, ds_def)
        self._dprint("[rrd] added DS %s to %s" % (dsname, fname))

    def add_point_to_rrd(self, fname, tpl, values, ts=None):
        """Try to add a new point to RRD file."""
        if ts:
            values = "{}:{}".format(ts, values)
        if self.verbose:
            print("[rrd] VERBOSE update -t %s %s" % (tpl, values))
        try:
            rrdtool.update(str(fname), "-t", tpl, values)
        except rrdtool.OperationalError as e:
            op_match = re.match(r"unknown DS name '(\w+)'", str(e))
            if op_match is None:
                raise
            self.add_datasource_to_rrd(str(fname), op_match.group(1))
            rrdtool.update(str(fname), "-t", tpl, values)

    def update_rrd(self, dom, t):
        """update_rrd

        Update RRD with records at t time.

        True  : if data are up-to-date for current minute
        False : syslog may have probably been already recorded
        or something wrong
        """
        fname = "%s/%s.rrd" % (self.workdir, dom)
        m = t - (t % rrdstep)

        self._dprint("[rrd] updating %s" % fname)
        if not os.path.exists(fname):
            self.lupdates[fname] = self.init_rrd(fname, m)
            self._dprint("[rrd] create new RRD file %s" % fname)
        else:
            if fname not in self.lupdates:
                self.lupdates[fname] = rrdtool.last(str(fname))

        if m <= self.lupdates[fname]:
            if self.verbose:
                print("[rrd] VERBOSE events at %s already recorded in RRD" % m)
            return False

        tpl = ""
        for v in variables:
            if tpl != "":
                tpl += ":"
            tpl += v
        # Missing some RRD steps
        # Est ce vraiment nécessaire... ?
        if m > self.lupdates[fname] + rrdstep:
            values = ""
            for v in variables:
                if values != "":
                    values += ":"
                values += "0"
            for p in range(self.lupdates[fname] + rrdstep, m, rrdstep):
                self.add_point_to_rrd(fname, tpl, values, ts=p)

        values = "%s" % m
        tpl = ""
        for v in variables:
            values += ":"
            values += str(self.data[dom][m][v])
            if tpl != "":
                tpl += ":"
            tpl += v
        self.add_point_to_rrd(fname, tpl, values)
        self.lupdates[fname] = m
        return True

    def initcounters(self, dom):
        init = {}
        for v in variables:
            init[v] = 0
        self.data[dom][self.cur_t] = init

    def inc_counter(self, dom, counter, val=1):
        if dom is not None and dom in self.domains:
            if self.cur_t not in self.data[dom]:
                self.initcounters(dom)
            self.data[dom][self.cur_t][counter] += val

        if self.cur_t not in self.data["global"]:
            self.initcounters("global")
        self.data["global"][self.cur_t][counter] += val

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
        month = time.strptime(month, "%b").tm_mon if not month.isdigit() \
            else int(month)
        if self.curmonth == 1 and month != self.curmonth:
            return self.__year - 1
        return self.__year

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
        else:
            return mail_address

    def _parse_amavis(self, log, host, pid, subprog):
        """ Parse an Amavis log entry.

        :param str log: logged message
        :param str host: hostname
        :param str pid: process ID
        :return: True on success
        """
        m = self._regex["amavis"].search(log)
        if m is not None:
            dom = m.group("domain")
            spam_result = m.group("result")
            if dom is not None and dom in self.domains:
                if spam_result == "INFECTED":
                    self.inc_counter(dom, "virus")
                elif spam_result in ["SPAM", "SPAMMY"]:
                    self.inc_counter(dom, "spam")
                return True

        return False

    def _parse_rmilter(self, log, host, pid, subprog):
        """ Parse an Rmilter log entry.

        :param str log: logged message
        :param str host: hostname
        :param str pid: process ID
        :return: True on success
        """
        m = self._regex["rmilter_line"].match(log)
        if m is None:
            return False
        rmilter_hash, msg = m.groups()
        workdict_key = "rmilter_" + rmilter_hash

        # Virus check must come before spam check due to pattern similarity.
        m = self._regex["rmilter_virus"].match(msg)
        if m is not None:
            self.workdict[workdict_key] = {
                "action": "virus"
            }
            return True
        m = self._regex["rmilter_spam"].match(msg)
        if m is not None:
            self.workdict[workdict_key] = {
                "action": "spam"
            }
            return True

        # Greylisting
        if self.greylist:
            m = self._regex["rmilter_greylist"].search(msg)
            if m is not None:
                self.workdict[workdict_key] = {
                    "action": "greylist"
                }
                return True

        # Gather information about message sender and queue ID
        m = self._regex["rmilter_msg_done"].match(msg)
        if m is not None:
            dom = split_mailbox(m.group("rcpt"))[1]

            if workdict_key in self.workdict:
                action = self.workdict[workdict_key].get("action", None)
                if action is not None:
                    self.inc_counter(dom, action)
            return True

        return False

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
                if condition:
                    self.inc_counter(dom, "greylist")
                else:
                    self.inc_counter(dom, "reject")
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
        if msg_status not in variables:
            self._dprint("[parser] unsupported status %s, skipping"
                         % msg_status)
            return True

        # orig_to is optional.
        m = self._regex["orig_to"].search(msg)
        msg_orig_to = m.group(1) if m is not None else None

        # Handle local "from" domains.
        from_domain = split_mailbox(self.workdict[queue_id]["from"])[1]
        if from_domain is not None and from_domain in self.domains:
            self.inc_counter(from_domain, "sent")
            self.inc_counter(from_domain, "size_sent",
                             self.workdict[queue_id]["size"])

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
            self.inc_counter(to_domain, "recv")
            self.inc_counter(to_domain, "size_recv",
                             self.workdict[queue_id]["size"])
        else:
            self.inc_counter(to_domain, msg_status)

        last_message = models.Maillog.objects.last()
        cur_dt = datetime.fromtimestamp(self.orig_ts)
        tz = timezone.get_current_timezone()
        cur_dt = tz.localize(cur_dt)
        condition = (
            last_message and (
                cur_dt < last_message.date or
                (cur_dt == last_message.date and
                 models.Maillog.objects.filter(
                     date=cur_dt, queue_id=queue_id).exists())
            )
        )
        if not condition:
            if from_domain in self.domains:
                from_domain = Domain.objects.filter(
                    Q(name=from_domain) |
                    Q(domainalias__name=from_domain)
                ).first()
            else:
                from_domain = None
            if to_domain in self.domains:
                to_domain = Domain.objects.filter(
                    Q(name=to_domain) |
                    Q(domainalias__name=to_domain)
                ).first()
            else:
                to_domain = None
            if msg_status == "sent" and to_domain:
                msg_status = "received"
            models.Maillog.objects.create(
                queue_id=queue_id,
                date=cur_dt,
                sender=self.workdict[queue_id]["from"],
                rcpt=msg_to,
                original_rcpt=msg_orig_to,
                size=self.workdict[queue_id]["size"],
                status=msg_status,
                from_domain=from_domain,
                to_domain=to_domain
            )

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
                "[parser] no log handler for \"{}\": {}".format(prog, log))

    def process(self):
        """Process the log file.

        We parse it and then generate standard graphics (day, week,
        month).
        """
        for line in self.f.readlines():
            self._parse_line(line)

        for dom, data in self.data.items():
            self._dprint("[rrd] dealing with domain %s" % dom)
            for t in sorted(data.keys()):
                self.update_rrd(dom, t)


class Command(BaseCommand):
    help = "Log file parser"

    def add_arguments(self, parser):
        """Add extra arguments to command line."""
        parser.add_argument(
            "--logfile", default=None,
            help="postfix log in syslog format", metavar="FILE")
        parser.add_argument(
            "--verbose", default=False, action="store_true",
            dest="verbose", help="Set verbose mode")
        parser.add_argument(
            "--debug", default=False, action="store_true",
            help="Set debug mode")

    def handle(self, *args, **options):
        if options["logfile"] is None:
            options["logfile"] = param_tools.get_global_parameter(
                "logfile", app="maillog")
        greylist = param_tools.get_global_parameter(
            "greylist", raise_exception=False)
        p = LogParser(
            options, param_tools.get_global_parameter("rrd_rootdir"),
            None, greylist
        )
        p.process()
