# coding: utf-8

from django.utils.translation import ugettext_lazy

class Graph(object):
    width = 540
    height = 120
    cf = 'AVERAGE'

    def __init__(self, **ds):
        self.vars = {}
        for dsname, dsdef in ds.iteritems():
            self.vars[dsname] = dsdef

    @property
    def display_name(self):
        return self.__class__.__name__.lower()

class AvgTraffic(Graph):
    title = ugettext_lazy('Average normal traffic')
    vertlabel = ugettext_lazy('msgs/min')
    
    def __init__(self):
        super(AvgTraffic, self).__init__(
            sent={'type' : 'AREA', 'color' : '#00FF00', 
                  "legend" : ugettext_lazy("sent messages")},
            recv={"type" : "AREA", "color" : "#0000FF", 
                  "legend" : ugettext_lazy("received messages")}
            )

class AvgBadTraffic(Graph):
    title = ugettext_lazy('Average bad traffic')
    vertlabel = ugettext_lazy('msgs/min')
    
    def __init__(self):
        super(AvgBadTraffic, self).__init__(
            bounced={'type' : 'AREA', 'color' : '#FFFF00', 
                     "legend" : ugettext_lazy("bounced messages")},
            reject={"type" : "AREA", "color" : "#FF0000", 
                    "legend" : ugettext_lazy("rejected messages")}
            )

class AvgTrafficSize(Graph):
    title = ugettext_lazy('Average normal traffic size')
    vertlabel = ugettext_lazy('bytes/min')
    
    def __init__(self):
        super(AvgTrafficSize, self).__init__(
            size_recv={'type' : 'AREA', 'color' : '#FF9900', 
                       "legend" : ugettext_lazy("received size")},
            size_sent={"type" : "AREA", "color" : "#339999", 
                       "legend" : ugettext_lazy("sent size")}
            )
            

class GraphSet(object):
    title = None
    graphs = []

    @property
    def html_id(self):
        return self.__class__.__name__.lower()

    def get_graphs(self):
        if not hasattr(self, '__graph_instances'):
            self.__graph_instances =  map(lambda gc: gc(), self.graphs)
        return self.__graph_instances

    def get_graph_names(self):
        return map(lambda g: g.display_name, self.get_graphs())

class MailTraffic(GraphSet):
    title = ugettext_lazy('Mail traffic')
    graphs = [AvgTraffic, AvgBadTraffic, AvgTrafficSize]
