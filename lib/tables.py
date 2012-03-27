# -*- coding: utf-8 -*-
"""
:mod:`tables` --- simple tabular renderer
-----------------------------------------

This module offers a simple (I hope so) interface to render tabular
data. For a given Table class, it generates the corresponding HTML
output (using standard tags like <table> and co.).

"""
import inspect
import lxml
from django.utils.translation import ugettext as _
from django.template import Template, RequestContext, Context
from django.template.loader import render_to_string

class Column:
    """Simple column representation
    """
    def __init__(self, name, **kwargs):
        self.name = name
        self.sortable = True
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
            
    def __str__(self):
        try:
            label = getattr(self, "label")
        except KeyError:
            label = getattr(self, "name")
        return _(label)


class SelectionColumn(Column):
    """Specific column: selection

    A 'selection' column contains only checkboxes (one per row). It is
    usefull to select rows for grouped actions (modify, delete, etc.)
    """
    def __str__(self):
        return "<input type='checkbox' name='selectall' id='selectall' />"

    def render(self, value, selection):
        return "<input type='checkbox' id='%s' name='select_%s' value='%s' %s/>" \
            % (self.name, value, value, selection and "checked" or "")

class ImgColumn(Column):
    """Specific column: image
    
    This kind of column only contains images tags (<img>).
    """
    def __str__(self):
        self.sortable = False
        try:
            return getattr(self, "header")
        except AttributeError:
            return ""

    def render(self, value):
        return "<img src='%s' />" % value

class DivColumn(Column):
    def __str__(self):
        return ""

    def render(self):
        return "<div>&nbsp;</div>"

class ActionColumn(Column):
    def render(self, fct, user, rowid):
        return fct(user, rowid)

class Table(object):
    tableid = ""

    def __init__(self, request, rows={}):
        self.columns = []
        self.request = request
        try:
            order = getattr(self, "cols_order")
        except AttributeError:
            for m in inspect.getmembers(self):
                if isinstance(m[1], Column):
                    try:
                        if getattr(m[1], "first"):
                            self.columns = [m[1]] + self.columns
                    except AttributeError:
                        self.columns += [m[1]]
        else:
            for colname in order:
                try:
                    col = getattr(self, colname)
                except AttributeError:
                    continue
                if not isinstance(col, Column):
                    continue
                self.columns += [col]

        if rows != {}:
            self.populate(rows)

    def populate(self, rows):
        self.rows = []
        trcpt = 0
        for row in rows:
            nrow = {"id" : row[self.idkey], "cols" : [], "trcpt" : trcpt}
            if row.has_key("options"):
                nrow["options"] = row["options"]
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
                    else:
                        try:
                            newcol["value"] = c.render(c.defvalue)
                        except Exception:
                            pass
                    newcol["safe"] = True
                elif isinstance(c, DivColumn):
                    newcol["value"] = c.render()
                    newcol["safe"] = True
                elif isinstance(c, ActionColumn):
                    newcol["value"] = c.render(c.defvalue, self.request.user, nrow["id"])
                    newcol["safe"] = True
                elif row.has_key(c.name):
                    if "class" in row.keys():
                        newcol["cssclass"] += newcol["cssclass"] != "" \
                            and ", %s" % row["class"] or row["class"]
                    try:
                        newcol["value"] = self.parse(c.name, row[c.name])
                    except AttributeError:
                        newcol["value"] = row[c.name]
                    try:
                        limit = getattr(c, "limit")
                        if len(newcol["value"]) > limit:
                            newcol["value"] = newcol["value"][0:limit] + "..."
                    except AttributeError:
                        pass
                    try:
                        newcol["safe"] = getattr(c, "safe")
                    except AttributeError:
                        pass
                nrow["cols"] += [newcol]
            self.rows += [nrow]
            trcpt += 1
            
    def _rows_from_model(self, objects, include_type_in_id=False):
        rows = []
        for obj in objects:
            nrow = {}
            try:
                idkey = getattr(self, "idkey")
                nrow[idkey] = getattr(obj, idkey)
                if include_type_in_id:
                    nrow[idkey] = "%s:%s" % (obj.__class__.__name__, nrow[idkey])
            except AttributeError:
                pass
            for c in self.columns:
                try:
                    nrow[c.name] = getattr(obj, c.name)
                except AttributeError:
                    pass
            for meth in ["options", "class"]:
                try:
                    nrow[meth] = getattr(self, "row_%s" % meth)(self.request, obj)
                except AttributeError:
                    pass
            rows += [nrow]
        return rows

    def parse(self, header, value):
        try:
            return getattr(self, "parse_%s" % header)(value)
        except AttributeError:
            return value

    def __str__(self):
        return self.render()

    def render(self, styles="table-striped table-bordered", withheader=True):
        if len(self.rows):
            t = Template("""
<table id="{{ tableid }}" class="table {{ styles }}">
  {% if withheader %}{% include "common/table_head.html" %}{% endif %}
  {% include "common/table_body.html" %}
</table>
""")
            return t.render(RequestContext(self.request, {
                        "table" : self, "tableid" : self.tableid, "styles" : styles,
                        "withheader" : withheader
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
                        
