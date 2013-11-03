# coding: utf-8
"""
:mod:`tables` --- simple tabular renderer
-----------------------------------------

This module offers a simple (I hope so) interface to render tabular
data. For a given Table class, it generates the corresponding HTML
output (using standard tags like <table> and co.).

"""
import inspect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.template import Template, RequestContext, Context
from templatetags.lib_tags import render_link


class Column(object):
    """Simple column representation
    """
    def __init__(self, name, **kwargs):
        self.name = name
        self.sortable = True
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __unicode__(self):
        try:
            label = getattr(self, "label")
        except AttributeError:
            return u''
        return label

    def transform(self, row, col, table):
        if "class" in row.keys():
            col["cssclass"] += col["cssclass"] != "" \
                and ", %s" % row["class"] or row["class"]
        try:
            col["value"] = table.parse(self.name, row[self.name])
        except AttributeError:
            col["value"] = row[self.name]
        try:
            limit = getattr(self, "limit")
            if limit:
                # The value is not necessarily a string, so...
                col["value"] = str(col["value"])
                if len(col["value"]) > limit:
                    col["value"] = col["value"][0:limit] + "..."
        except AttributeError:
            pass
        try:
            col["safe"] = getattr(self, "safe")
        except AttributeError:
            pass


class SelectionColumn(Column):
    """Specific column: selection

    A 'selection' column contains only checkboxes (one per row). It is
    usefull to select rows for grouped actions (modify, delete, etc.)
    """
    def __unicode__(self):
        if self.header:
            return "<input type='checkbox' name='selectall' id='selectall' />"
        return ""

    def render(self, value, selection):
        return "<input type='checkbox' id='%(id)s' name='select_%(value)s' value='%(value)s' %(checked)s/>" \
            % {'id': self.name, 'value': value,
               "checked": "checked=''" if selection else ""}

    def transform(self, row, col, table):
        selection = row[self.name] if self.name in row else False
        col["value"] = self.render(row[table.idkey], selection)
        col["safe"] = True


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
        if type(value) in [list, tuple]:
            return "".join(["<img src='%s' />" % i for i in value])
        return "<img src='%s' />" % value

    def transform(self, row, col, table):
        key = "img_%s" % self.name
        if key in row.keys():
            col["value"] = self.render(row[key])
        else:
            try:
                col["value"] = self.render(self.defvalue)
            except Exception:
                pass
        col["safe"] = True


class DivColumn(Column):
    def __str__(self):
        return ""

    def render(self):
        return "<div>&nbsp;</div>"

    def transform(self, row, col, table):
        col["value"] = self.render()
        col["safe"] = True


class ActionColumn(Column):
    def render(self, fct, user, rowid):
        return fct(user, rowid)

    def transform(self, row, col, table):
        col["value"] = self.render(self.defvalue, table.request.user, row[table.idkey])
        col["safe"] = True


class LinkColumn(Column):
    def render(self, rowid, value):
        linkdef = dict(label=value, modal=self.modal)
        if type(self.urlpattern) is dict:
            t, value = rowid.split(":")
            linkdef.update(url=reverse(self.urlpattern[t], args=[value]),
                           modalcb=self.modalcb[t])
        else:
            linkdef.update(url=reverse(self.urlpattern, args=[rowid]),
                           modalcb=self.modalcb)
        return render_link(linkdef)

    def transform(self, row, col, table):
        col["value"] = self.render(row[table.idkey], row[self.name])
        col["safe"] = True


class Table(object):
    tableid = ""

    def __init__(self, request, rows=None):
        self.columns = []
        self.request = request
        if rows is None:
            rows = {}
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
            nrow = {"id": row[self.idkey], "cols": [], "trcpt": trcpt}
            for name in ["style", "options"]:
                if name in row:
                    nrow[name] = row[name]

            for c in self.columns:
                newcol = {"name": c.name}
                for key in ["width", "align", "cssclass"]:
                    try:
                        newcol[key] = getattr(c, key)
                    except AttributeError:
                        newcol[key] = ""
                c.transform(row, newcol, self)
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

    def __unicode__(self):
        return self.render()

    def render(self, withheader=True):
        if len(self.rows):
            try:
                styles = self.styles
            except AttributeError:
                styles = "table-striped table-bordered"

            t = Template("""
<table id="{{ tableid }}" class="table {{ styles }}">
  {% if withheader %}{% include "common/table_head.html" %}{% endif %}
  {% include "common/table_body.html" %}
</table>
""")
            return t.render(RequestContext(self.request, {
                "table": self, "tableid": self.tableid, "styles": styles,
                "withheader": withheader
            }))

        t = Template("""
<div class="alert alert-info">%s</div>
""" % _("No entries to display"))
        return t.render(Context())
