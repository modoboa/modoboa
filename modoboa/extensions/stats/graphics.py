import os
import inspect
from lxml import etree
from django.utils.translation import ugettext_lazy
from modoboa.lib import parameters
from modoboa.lib.sysutils import exec_cmd


class Curve(object):
    """Graphic curve.

    Simple way to represent a graphic curve.
    """
    def __init__(self, dsname, color, legend, cfunc="AVERAGE"):
        """Constructor.
        """
        self.dsname = dsname
        self.color = color
        self.legend = legend.encode("utf-8")
        self.cfunc = cfunc

    def to_rrd_command_args(self, rrdfile):
        """Convert this curve to the approriate RRDtool command.

        :param str rrdfile: RRD file name
        :return: a list
        """
        rrdfile = os.path.join(
            parameters.get_admin("RRD_ROOTDIR"), "%s.rrd" % rrdfile
        )
        return [
            'DEF:%s=%s:%s:%s' %
            (self.dsname, rrdfile, self.dsname, self.cfunc),
            'CDEF:%(ds)spm=%(ds)s,60,*' % {"ds": self.dsname},
            'XPORT:%spm:"%s"' % (self.dsname, self.legend.decode("utf-8"))
        ]


class Graphic(object):
    """Graphic.

    """
    def __init__(self):
        """Constructor.
        """
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

    def export(self, rrdfile, start, end):
        """
        """
        result = []
        cmdargs = []
        for curve in self._curves:
            result += [{
                "name": curve.legend, "color": curve.color, "data": []
            }]
            cmdargs += curve.to_rrd_command_args(rrdfile)
        cmd = "rrdtool xport --start %s --end %s " % (str(start), str(end))
        cmd += " ".join(cmdargs)
        if type(cmd) is unicode:
            cmd = cmd.encode("utf-8")
        code, output = exec_cmd(cmd)
        if code:
            return []
        tree = etree.fromstring(output)
        for row in tree.xpath('/xport/data/row'):
            timestamp = int(row.find('t').text)
            for vindex, value in enumerate(row.findall('v')):
                if value.text == 'NaN':
                    result[vindex]['data'].append({'x': timestamp, 'y': 0})
                else:
                    result[vindex]['data'].append(
                        {'x': timestamp, 'y': float(value.text)}
                    )
        return result


class AverageTraffic(Graphic):
    """Average traffic.
    """
    title = ugettext_lazy('Average traffic (msgs/min)')

    # Curve definitions
    sent = Curve("sent", "lawngreen", ugettext_lazy("sent messages"))
    recv = Curve("recv", "steelblue", ugettext_lazy("received messages"))
    bounced = Curve("bounced", "yellow", ugettext_lazy("bounced messages"))
    reject = Curve("reject", "tomato", ugettext_lazy("rejected messages"))

    order = ['reject', 'bounced', 'recv', 'sent']


class AverageTrafficSize(Graphic):
    """Average traffic size.
    """
    title = ugettext_lazy('Average normal traffic size (bytes/min)')

    # Curve definitions
    size_recv = Curve("size_recv", "orange", ugettext_lazy("received size"))
    size_sent = Curve(
        "size_sent", "mediumturquoise", ugettext_lazy("sent size")
    )


class GraphicSet(object):
    title = None
    _graphics = []

    def __init__(self):
        self.__ginstances = []

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

    def export(self, rrdfile, start, end):
        result = {}
        for graph in self.graphics:
            result[graph.display_name] = {
                "title": graph.title.encode("utf-8"),
                "curves": graph.export(rrdfile, start, end)
            }
        return result


class MailTraffic(GraphicSet):
    title = ugettext_lazy('Mail traffic')
    _graphics = [AverageTraffic, AverageTrafficSize]
