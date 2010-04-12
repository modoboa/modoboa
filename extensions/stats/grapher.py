# -*- coding: utf-8 -*-

import os
import time
import datetime
import rrdtool
from django.utils.translation import ugettext as _
from mailng.lib import getoption

traffic_avg_template = {
    'name' : 'traffic',
    'width'  : '540',
    'height' : '100',
    'vertlabel' : 'msgs/min',
    'cf' : 'AVERAGE',
    'vars' : {
        'sent' : { "type" : "AREA", "color" : "#00FF00", 
                   "legend" : _("sent messages") },
        'recv' : { "type" : "AREA", "color" : "#0000FF", 
                   "legend" : _("received messages") },
        }
}

badtraffic_avg_template = {
    'name' : 'badtraffic',
    'width'  : '540',
    'height' : '100',
    'vertlabel' : _('msgs/min'),
    'cf' : 'AVERAGE',
    'vars' : {
        'bounced' : { "type" : "AREA", "color" : "#FFFF00", 
                      "legend" : _("bounced messages") },
        'reject' : { "type" : "AREA", "color" : "#FF0000", 
                     "legend" : _("rejected messages") },
        }
}

size_avg_template = {
    'name' : 'size',
    'width'  : '540',
    'height' : '100',
    'vertlabel' : _('bytes/min'),
    'cf' : 'AVERAGE',
    'vars' : {
        'size_recv' : { "type" : "AREA", "color" : "#FF9900", 
                        "legend" : _("received size") },
        'size_sent' : { "type" : "AREA", "color" : "#339999", 
                        "legend" : _("sent size") },
        }
}

tpl = {'traffic':traffic_avg_template,
       'badtraffic':badtraffic_avg_template,
       'size':size_avg_template}

class Grapher(object):
    def __init__(self):
        self.rrd_rootdir = getoption("RRD_ROOTDIR", "/tmp")
        self.img_rootdir = getoption("IMG_ROOTDIR", "/tmp")

    def process(self, target, suffix, start, end, tpl=traffic_avg_template):
        rrdfile = "%s/%s.rrd" % (self.rrd_rootdir, target)
        if not os.path.exists(rrdfile):
            print "[graph] no rrd file %s detected" %rrdfile
            return
        ext = "png"
        path = "%s/%s_%s_%s_%s.%s" % (self.img_rootdir, tpl['name'],
                                      target, tpl['cf'], suffix, ext)
        start = str(start)
        end = str(end)
        defs = []
        lines = []
        for v, d in tpl["vars"].iteritems():
            defs += ['DEF:%s=%s:%s:%s' % (v, rrdfile, v, tpl['cf']),
                     'CDEF:%spm=%s,60,*' % (v, v)]
            type = d.has_key("type") and d["type"] or "LINE"
            lines += ["%s:%spm%s:%s" % (type, v, d["color"],
                                        d["legend"].encode("utf-8"))]
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
                      *params)

        if not os.path.exists(path):
            print "[graph] Impossible to create %s graph" %path
        else:
            print "[graph] %s graph created" %path

    def make_defaults(self, target, tpl=traffic_avg_template):
        end = "%d" % int(time.mktime(time.localtime()))
        self.process(target, "day", "-1day", end, tpl)
        self.process(target, "week", "-1week", end, tpl)
        self.process(target, "month", "-1month", end, tpl)
        self.process(target, "year", "-1year", end, tpl)
        
        
