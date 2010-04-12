# -*- coding: utf-8 -*-
import inspect
import lxml
from django.template import Template, Context
from django.template.loader import render_to_string

class Column:
    sortable = True

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
    sortable = False

    def __str__(self):
        try:
            return getattr(self, "header")
        except AttributeError:
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
                newcol = {}
                try:
                    newcol["width"] = getattr(c, "width")
                except AttributeError:
                    pass
                if isinstance(c, SelectionColumn):
                    newcol["value"] = c.render(row[self.idkey])
                    newcol["safe"] = True

                if isinstance(c, ImgColumn):
                    key = "img_%s" % c.name
                    if key in row.keys():
                        newcol["value"] = c.render(row[key])
                        newcol["safe"] = True

                if row.has_key(c.name):
                    try:
                        cssclass = getattr(c, "cssclass")
                    except AttributeError:
                        cssclass = ""
                    if "class" in row.keys():
                        cssclass += (cssclass != "") and ", %s" % row["class"] or row["class"]
                    newcol["value"] = self.parse(c.name, row[c.name])
                    newcol["class"] = cssclass
                nrow["cols"] += [newcol]
            self.rows += [nrow]

    def render(self, request):
        t = Template("""
<table id="{{ tableid }}">
  {% include "common/table_head.html" %}
  {% include "common/table_body.html" %}
</table>
""")
        return t.render(Context({
                    "table" : self, "tableid" : self.tableid
                    }))

    def render_head(self, request):
        t = Template("""
<table id="{{ tableid }}">
  {% include "common/table_head.html" %}
</table>
""")
        return t.render(Context({
                    "table" : self, "tableid" : "%s_head" % self.tableid
                    }))
    
    def render_body(self, request):
        t = Template("""
<table id="{{ tableid }}">
  {% include "common/table_body.html" %}
</table>
""")
        return t.render(Context({
                    "table" : self, "tableid" : "%s_body" % self.tableid
                    }))
                        
