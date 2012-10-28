# coding: utf-8

import sys, os
import time
import datetime
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.lib import parameters

def str2Time(y, M, d, h="0", m="0", s="0"):
    """Date conversion

    Returns a date and a time in seconds from the epoch.

    :return: an integer
    """
    try:
        if not M.isdigit():
            local = time.strptime("%s %s %s %s:%s:%s" % (y, M, d, h, m, s), \
                                      "%Y %b %d %H:%M:%S")
        else:
            local = time.strptime("%s %s %s %s:%s:%s" % (y, M, d, h, m, s), \
                                      "%Y %m %d %H:%M:%S")
    except ValueError:
        print >>sys.stderr, "Error: failed to convert date and time"
        return 0

    return int(time.mktime(local))

class Grapher(object):
    def __init__(self):
        self.rrd_rootdir = parameters.get_admin("RRD_ROOTDIR")
        self.img_rootdir = parameters.get_admin("IMG_ROOTDIR")

    def process(self, target, suffix, start, end, tpl):
        import rrdtool

        rrdfile = "%s/%s.rrd" % (self.rrd_rootdir, target)
        if not os.path.exists(rrdfile):
            return
        ext = "png"
        path = "%s/%s_%s_%s_%s.%s" % (self.img_rootdir, tpl['name'],
                                      target, tpl['cf'], suffix, ext)
        start = str(start)
        end = str(end)
        defs = []
        lines = []
        defs.append('COMMENT: %s %s %s %s\\c' % ("From", start, "to", end))
        defs.append('COMMENT:\\s')
        for v, d in tpl["vars"].iteritems():
            defs += [str('DEF:%s=%s:%s:%s' % (v, rrdfile, v, tpl['cf'])),
                     str('CDEF:%spm=%s,60,*' % (v, v)),
                     str('VDEF:%s_total=%s,TOTAL' % (v, v))]
            type = d.has_key("type") and d["type"] or "LINE"
            lines += [str("%s:%spm%s:%s:STACK" % (type, v, d["color"],
                                                  (d["legend"].encode("utf8")).ljust(20)))]
            lines.append('GPRINT:%s_total:%s%%7.0lf%%s\\l' % (v, _("Total").encode('utf-8')))

        params = defs + lines
        rrdtool.graph(str(path),
                      "--imgformat", "PNG",
                      "--width", tpl["width"],
                      "--height", tpl["height"],
                      "--start", start,
                      "--end", end,
                      "--vertical-label", tpl["vertlabel"].encode("utf-8"),
                      "--lower-limit", "0",
                      "--slope-mode",
                      "--units-exponent", "0",
                      "--title", tpl["title"].encode("utf-8"),
                      *params)

        if not os.path.exists(path):
            print "[graph] Impossible to create %s graph" %path

    def make_defaults(self, target, tpl):
        end = "%d" % int(time.mktime(time.localtime()))
        self.process(target, "day", "-1day", end, tpl)
        self.process(target, "week", "-1week", end, tpl)
        self.process(target, "month", "-1month", end, tpl)
        self.process(target, "year", "-1year", end, tpl)
        
        
