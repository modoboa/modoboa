# -*- coding: utf-8 -*-
import inspect
import lxml
from django.utils.translation import ugettext as _
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

    def render(self, value, selection):
        return "<input type='checkbox' id='%s' name='select_%s' value='%s' %s/>" \
            % (self.name, value, value, selection and "checked" or "")

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
        trcpt = 0
        for row in rows:
            nrow = {"id" : row[self.idkey], "cols" : [], "trcpt" : trcpt}
            for c in self.columns:
                newcol = {"name" : c.name}
                for key in ["width", "align", "cssclass"]:
                    try:
                        newcol[key] = getattr(c, key)
                    except AttributeError:
                        newcol[key] = ""
                if isinstance(c, SelectionColumn):
                    selection = row.has_key(c.name) and row[c.name] or False
                    newcol["value"] = c.render(row[self.idkey], selection)
                    newcol["safe"] = True                  
                elif isinstance(c, ImgColumn):
                    key = "img_%s" % c.name
                    if key in row.keys():
                        newcol["value"] = c.render(row[key])
                        newcol["safe"] = True
                elif row.has_key(c.name):
                    if "class" in row.keys():
                        newcol["cssclass"] += newcol["cssclass"] != "" \
                            and ", %s" % row["class"] or row["class"]
                    try:
                        newcol["value"] = self.parse(c.name, row[c.name])
                    except AttributeError:
                        newcol["value"] = row[c.name]
                nrow["cols"] += [newcol]
            self.rows += [nrow]
            trcpt += 1

    def render(self, request):
        if len(self.rows):
            t = Template("""
<table id="{{ tableid }}">
  {% include "common/table_head.html" %}
  {% include "common/table_body.html" %}
</table>
""")
            return t.render(Context({
                        "table" : self, "tableid" : self.tableid
                        }))
        t = Template("""
<div class="info">%s</div>
""" % _("No entries to display"))
        return t.render(Context())

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
                        
