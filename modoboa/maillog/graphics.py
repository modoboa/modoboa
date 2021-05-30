"""Classes to define graphics."""

import datetime
import json
import inspect
from itertools import chain
import os

from django.conf import settings
from django.utils.encoding import smart_bytes, smart_text
from django.utils.translation import ugettext as _, ugettext_lazy

from modoboa.admin import models as admin_models
from modoboa.lib import exceptions
from modoboa.lib.sysutils import exec_cmd
from modoboa.parameters import tools as param_tools


class Curve:
    """Graphic curve.

    Simple way to represent a graphic curve.
    """

    def __init__(self, dsname, color, legend, cfunc="AVERAGE"):
        """Constructor.
        """
        self.dsname = dsname
        self.color = color
        self.legend = legend
        self.cfunc = cfunc

    def to_rrd_command_args(self, rrdfile):
        """Convert this curve to the approriate RRDtool command.

        :param str rrdfile: RRD file name
        :return: a list
        """
        rrdfile = os.path.join(
            param_tools.get_global_parameter("rrd_rootdir"), "%s.rrd" % rrdfile
        )
        return [
            'DEF:%s=%s:%s:%s' %
            (self.dsname, rrdfile, self.dsname, self.cfunc),
            'CDEF:%(ds)spm=%(ds)s,UN,0,%(ds)s,IF,60,*' % {"ds": self.dsname},
            'XPORT:%spm:"%s"' % (self.dsname, self.legend)
        ]


class Graphic:
    """Graphic."""

    def __init__(self):
        """Constructor."""
        self._curves = []
        try:
            order = getattr(self, "order")
        except AttributeError:
            for member in inspect.getmembers(self):
                if isinstance(member[1], Curve):
                    self._curves += [member[1]]
        else:
            for name in order:
                try:
                    curve = getattr(self, name)
                except AttributeError:
                    continue
                if not isinstance(curve, Curve):
                    continue
                self._curves += [curve]

    @property
    def display_name(self):
        return self.__class__.__name__.lower()

    @property
    def rrdtool_binary(self):
        """Return path to rrdtool binary."""
        dpath = None
        code, output = exec_cmd("which rrdtool")
        if not code:
            dpath = output.strip()
        else:
            known_paths = getattr(
                settings, "RRDTOOL_LOOKUP_PATH",
                ("/usr/bin/rrdtool", "/usr/local/bin/rrdtool")
            )
            for fpath in known_paths:
                if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
                    dpath = fpath
        if dpath is None:
            raise exceptions.InternalError(
                _("Failed to locate rrdtool binary."))
        return smart_text(dpath)

    def export(self, rrdfile, start, end):
        """Export data to JSON using rrdtool."""
        result = []
        cmdargs = []
        for curve in self._curves:
            result += [{
                "name": str(curve.legend),
                "backgroundColor": curve.color, "data": []
            }]
            cmdargs += curve.to_rrd_command_args(rrdfile)
        code = 0

        cmd = "{} xport --json -t --start {} --end {} ".format(
            self.rrdtool_binary, str(start), str(end))
        cmd += " ".join(cmdargs)
        code, output = exec_cmd(smart_bytes(cmd))
        if code:
            return []

        xport = json.loads(output)
        for row in xport['data']:
            timestamp = int(row[0])
            date = datetime.datetime.fromtimestamp(timestamp).isoformat(sep=' ')
            for (vindex, value) in enumerate(row[1:]):
                result[vindex]['data'].append(
                    {'x': date, 'y': value, 'timestamp': timestamp}
                )

        return result


class GraphicSet(object):
    """A set of graphics."""

    domain_selector = False
    title = None
    _graphics = []

    def __init__(self, instances=None):
        if instances is None:
            instances = []
        self.__ginstances = instances

    @property
    def html_id(self):
        return self.__class__.__name__.lower()

    @property
    def graphics(self):
        if not self.__ginstances:
            self.__ginstances = [graphic() for graphic in self._graphics]
        return self.__ginstances

    def get_graphic_names(self):
        return [graphic.display_name for graphic in self._graphics]

    def get_file_name(self, request, searchq):
        """Return database file name."""
        return self.file_name

    def export(self, rrdfile, start, end, graphic=None):
        result = {}
        for graph in self.graphics:
            if graphic is None or graphic == graph.display_name:
                result[graph.display_name] = {
                    "title": str(graph.title),
                    "series": graph.export(rrdfile, start, end)
                }
        return result


class AverageTraffic(Graphic):
    """Average traffic."""

    title = ugettext_lazy('Average traffic (msgs/min)')

    # Curve definitions
    sent = Curve("sent", "lawngreen", ugettext_lazy("sent messages"))
    recv = Curve("recv", "steelblue", ugettext_lazy("received messages"))
    bounced = Curve("bounced", "yellow", ugettext_lazy("bounced messages"))
    reject = Curve("reject", "tomato", ugettext_lazy("rejected messages"))
    virus = Curve("virus", "orange", ugettext_lazy("virus messages"))
    spam = Curve("spam", "silver", ugettext_lazy("spam messages"))

    order = ["reject", "bounced", "recv", "sent", "virus", "spam"]

    def __init__(self, greylist=False):
        if greylist:
            self.greylist = Curve(
                "greylist", "dimgrey", ugettext_lazy("greylisted messages"))
            self.order = [
                "reject", "greylist", "bounced", "recv", "sent", "virus",
                "spam"
            ]
        super().__init__()


class AverageTrafficSize(Graphic):
    """Average traffic size."""

    title = ugettext_lazy('Average normal traffic size (bytes/min)')

    # Curve definitions
    size_recv = Curve("size_recv", "orange", ugettext_lazy("received size"))
    size_sent = Curve(
        "size_sent", "mediumturquoise", ugettext_lazy("sent size")
    )


class MailTraffic(GraphicSet):
    """Mail traffic graphic set."""

    domain_selector = True
    title = ugettext_lazy("Mail traffic")
    _graphics = [AverageTraffic, AverageTrafficSize]

    def __init__(self, greylist=False):
        instances = [AverageTraffic(greylist), AverageTrafficSize()]
        super().__init__(instances)

    def _check_domain_access(self, user, pattern):
        """Check if an administrator can access a domain.

        If a non super administrator asks for the global view, we give him
        a view on the first domain he manage instead.

        :return: a domain name (str) or None.
        """
        if pattern in [None, "global"]:
            if not user.is_superuser:
                domains = admin_models.Domain.objects.get_for_admin(user)
                if not domains.exists():
                    return None
                return domains.first().name
            return "global"

        results = list(
            chain(
                admin_models.Domain.objects.filter(name__startswith=pattern),
                admin_models.DomainAlias.objects.filter(
                    name__startswith=pattern)
            )
        )
        if len(results) != 1:
            return None
        if not user.can_access(results[0]):
            raise exceptions.PermDeniedException
        return results[0].name

    def get_file_name(self, user, searchq):
        """Retrieve file name according to user and args."""
        return self._check_domain_access(user, searchq)


class AccountCreationGraphic(Graphic):
    """Account creation over time."""

    title = ugettext_lazy("Average account creation (account/hour)")

    accounts = Curve(
        "new_accounts", "steelblue", ugettext_lazy("New accounts"))


class AccountGraphicSet(GraphicSet):
    """A graphic set for accounts."""

    file_name = "new_accounts"
    title = ugettext_lazy("Accounts")
    _graphics = [AccountCreationGraphic]
