# -*- coding: utf-8 -*-

import os
import time
import datetime
import rrdtool
from mailng.lib import getoption

default_avg_template = {
    'width'  : '540',
    'height' : '100',
    'title'  : 'average message flow per minute',
    'vertlabel' : 'msgs/min',
    'cf' : 'AVERAGE',
    'vars' : {
        'sent' : { "type" : "AREA", "color" : "#00FF00", "legend" : "sent messages" },
        'recv' : { "type" : "AREA", "color" : "#0000FF", "legend" : "received messages" },
#         'bounced' : { "color" : "#FFFF00", "legend" : "bounced messages" },
#         'reject' : { "color" : "#FF0000", "legend" : "rejected messages" },
        }
}

class Grapher(object):
    def __init__(self):
        self.rrd_rootdir = getoption("RRD_ROOTDIR", "/tmp")
        self.img_rootdir = getoption("IMG_ROOTDIR", "/tmp")

    def process(self, target, suffix, start, end, tpl=default_avg_template):
        rrdfile = "%s/%s.rrd" % (self.rrd_rootdir, target)
        if not os.path.exists(rrdfile):
            return
        ext = "png"
        path = "%s/%s_%s_%s.%s" % (self.img_rootdir, target, tpl['cf'], suffix, ext)
        start = str(start)
        end = str(end)
        defs = []
        lines = []
        for v, d in tpl["vars"].iteritems():
            defs += ['DEF:%s=%s:%s:%s' % (v, rrdfile, v, tpl['cf']),
                     'CDEF:%spm=%s,60,*' % (v, v)]
            type = d.has_key("type") and d["type"] or "LINE"
            lines += ["%s:%spm%s:%s" % (type, v, d["color"], d["legend"])]
        params = defs + lines
        rrdtool.graph(path,
                      "--imgformat", "PNG",
                      "--width", tpl["width"],
                      "--height", tpl["height"],
                      "--start", start,
                      "--end", end,
                      "--vertical-label", tpl["vertlabel"],
                      "--title", tpl["title"],
                      "--lower-limit", "0",
                      "--slope-mode",
                      *params)

    def make_defaults(self, target):
        #now = int(time.time())
        #start = now - (now % 86400)
        #end = start + 86400
        end = "now"
        self.process(target, "day", "-1day", end)

        #today = datetime.date.today()
        #day = today.day - today.weekday()
        #weekbegin = datetime.date(today.year, today.month, day)
        #start = weekbegin.strftime("%Y%m%d")
        #end = "+1week"
        self.process(target, "week", "-1week", end)

#         monthbegin = datetime.date(today.year, today.month, 1)
#         start = monthbegin.strftime("%Y%m%d")
#         end = "+1month"
        self.process(target, "month", "-1month", end)
        self.process(target, "year", "-1year", end)
        
        
