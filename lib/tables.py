# -*- coding: utf-8 -*-
import inspect
import lxml
from django.template.loader import render_to_string

class Column:
    def __init__(self, name, **kwargs):
        self.name = name
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
            
    def __str__(self):
        try:
            label = getattr(self, "label")
        except KeyError:
            label = getattr(self, "name")
        return label

class SelectionColumn(Column):
    def __str__(self):
        return "<input type='checkbox' name='selectall' id='selectall' />"

    def render(self, value):
        return "<input type='checkbox' name='%s' value='%s' />" \
            % (self.name, value)

class ImgColumn(Column):
    def __str__(self):
        return ""

    def render(self, value):
        return "<img src='%s' />" % value

class Table(object):
    tableid = ""

    def __init__(self, rows={}):
        self.columns = []
        for m in inspect.getmembers(self):
            if isinstance(m[1], Column):
                try:
                    if getattr(m[1], "first"):
                        self.columns = [m[1]] + self.columns
                except AttributeError:
                    self.columns += [m[1]]
        self.rows = []
        for row in rows:
            nrow = {"id" : row[self.idkey], "cols" : []}
            for c in self.columns:
                if isinstance(c, SelectionColumn):
                    nrow["cols"] += [{"value" : c.render(row[self.idkey]), "safe" : True}]
                    continue
                if isinstance(c, ImgColumn):
                    key = "img_%s" % c.name
                    if key in row.keys():
                        nrow["cols"] += [{"value" : c.render(row[key]), "safe" : True}]
                    else:
                        nrow["cols"] += ["."]
                    continue
                if row.has_key(c.name):
                    if "class" in row.keys():
                        cssclass = row["class"]
                    else:
                        cssclass = ""
                    
                    nrow["cols"] += [{"value" : self.parse(c.name, row[c.name]), 
                                      "class" : cssclass}]
            self.rows += [nrow]

    def render(self, request):
        return render_to_string("common/tables.html", {
                "table" : self, "tableid" : self.tableid
                })
