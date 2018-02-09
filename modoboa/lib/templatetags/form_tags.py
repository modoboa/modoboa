# -*- coding: utf-8 -*-

"""
Form rendering tags.
"""

from __future__ import unicode_literals

from django import forms, template
from django.template.loader import render_to_string
from django.utils.encoding import smart_text
from django.utils.safestring import mark_safe

from modoboa.lib.form_utils import SeparatorField

register = template.Library()


@register.simple_tag
def render_form(form, tpl=None):
    """Render a form."""
    if tpl is not None:
        return render_to_string(tpl, {"form": form})

    ret = ""
    for field in form:
        ret += "%s\n" % render_field(field)
    return mark_safe(ret)


def configure_field_classes(field):
    """Add required CSS classes to field."""
    if isinstance(field.field.widget, forms.CheckboxInput) or \
       isinstance(field.field.widget, forms.RadioSelect):
        return
    if "class" in field.field.widget.attrs:
        field.field.widget.attrs["class"] += " form-control"
    else:
        field.field.widget.attrs["class"] = "form-control"


@register.simple_tag
def render_field(
        field, help_display_mode="tooltip", label_width="col-sm-4",
        **options):
    """Render a field."""
    from modoboa.core.templatetags.core_tags import visirule

    if isinstance(field.field, SeparatorField):
        return "<h5%s>%s</h5>" % (visirule(field), smart_text(field.label))
    configure_field_classes(field)
    context = {
        "field": field, "help_display_mode": help_display_mode,
        "label_width": label_width, "deactivate_if_empty": True
    }
    context.update(options)
    return render_to_string("common/generic_field.html", context)


@register.simple_tag
def render_fields_group(form, pattern):
    """Render a group of fields."""
    first = forms.forms.BoundField(form, form.fields[pattern], pattern)
    configure_field_classes(first)
    label = first.label
    group = [first]
    cpt = 1
    haserror = len(first.errors) != 0
    while True:
        fname = "%s_%d" % (pattern, cpt)
        if fname not in form.fields:
            break
        bfield = forms.forms.BoundField(form, form.fields[fname], fname)
        if len(bfield.errors):
            haserror = True
        configure_field_classes(bfield)
        group += [bfield]
        cpt += 1

    return render_to_string(
        "common/generic_fields_group.html",
        {"label": label, "help_text": first.help_text, "group": group,
         "haserror": haserror, "pattern": pattern}
    )


@register.simple_tag
def render_field_width(field):
    """."""
    form = field.form
    if hasattr(form, "field_widths") and field.name in form.field_widths:
        width = form.field_widths[field.name]
    else:
        width = 5
    return "col-sm-{0}".format(width)
