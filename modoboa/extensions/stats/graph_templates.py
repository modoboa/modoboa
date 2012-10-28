# coding: utf-8

from django.utils.translation import ugettext_lazy

class MailTrafic(object):
    pass

traffic_avg_template = {
    'name' : 'traffic',
    'title' : ugettext_lazy("Average normal traffic"),
    'width'  : '540',
    'height' : '120',
    'vertlabel' : ugettext_lazy('msgs/min'),
    'cf' : 'AVERAGE',
    'vars' : {
        'sent' : { "type" : "AREA", "color" : "#00FF00", 
                   "legend" : ugettext_lazy("sent messages") },
        'recv' : { "type" : "AREA", "color" : "#0000FF", 
                   "legend" : ugettext_lazy("received messages") },
        }
}

badtraffic_avg_template = {
    'name' : 'badtraffic',
    'title' : ugettext_lazy("Average bad traffic"),
    'width'  : '540',
    'height' : '120',
    'vertlabel' : ugettext_lazy('msgs/min'),
    'cf' : 'AVERAGE',
    'vars' : {
        'bounced' : { "type" : "AREA", "color" : "#FFFF00", 
                      "legend" : ugettext_lazy("bounced messages") },
        'reject' : { "type" : "AREA", "color" : "#FF0000", 
                     "legend" : ugettext_lazy("rejected messages") },
        }
}

size_avg_template = {
    'name' : 'size',
    'title' : ugettext_lazy("Average normal traffic size"),
    'width'  : '540',
    'height' : '120',
    'vertlabel' : ugettext_lazy('bytes/min'),
    'cf' : 'AVERAGE',
    'vars' : {
        'size_recv' : { "type" : "AREA", "color" : "#FF9900", 
                        "legend" : ugettext_lazy("received size") },
        'size_sent' : { "type" : "AREA", "color" : "#339999", 
                        "legend" : ugettext_lazy("sent size") },
        }
}
