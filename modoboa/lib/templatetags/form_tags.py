"""
Form rendering tags.
"""

from django import forms
from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy

from modoboa.lib.formutils import SeparatorField

register = template.Library()


@register.simple_tag
def render_form(form, tpl=None):
    """Render a form."""
    if tpl is not None:
        return render_to_string(tpl, dict(form=form))

    ret = ""
    for field in form:
        ret += "%s\n" % render_field(field)
    return ret


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
def render_field(field, help_display_mode="tooltip"):
    """Render a field."""
    from modoboa.core.templatetags.core_tags import visirule

    if type(field.field) is SeparatorField:
        return "<h5%s>%s</h5>" % (visirule(field), unicode(field.label))
    configure_field_classes(field)
    return render_to_string("common/generic_field.html", dict(
        field=field, help_display_mode=help_display_mode
    ))


@register.simple_tag
def render_field_appended(field, text):
    configure_field_classes(field)
    return render_to_string("common/generic_field.html", dict(
        field=field, help_display_mode="tooltip", appended_text=text
    ))


@register.simple_tag
def render_field_with_activator(field, activator_label=ugettext_lazy("activate")):
    return render_to_string("common/generic_field.html", {
        "field": field, "help_display_mode": "tooltip", "activator": True,
        "activator_label": activator_label, "deactivate_if_empty": True
    })


@register.simple_tag
def render_and_hide_field(field):
    return render_to_string("common/generic_field.html", dict(
        field=field, hidden=True
    ))


@register.simple_tag
def render_fields_group(form, pattern):
    first = forms.BoundField(form, form.fields[pattern], pattern)
    configure_field_classes(first)
    label = first.label
    group = [first]
    cpt = 1
    haserror = len(first.errors) != 0
    while True:
        fname = "%s_%d" % (pattern, cpt)
        if not fname in form.fields:
            break
        bfield = forms.BoundField(form, form.fields[fname], fname)
        if len(bfield.errors):
            haserror = True
        configure_field_classes(bfield)
        group += [bfield]
        cpt += 1

    return render_to_string("common/generic_fields_group.html", dict(
        label=label, help_text=first.help_text, group=group, haserror=haserror
    ))


@register.simple_tag
def render_extra_fields(form):
    result = ''
    for fname in form.extra_fields:
        result += render_to_string("common/generic_field.html", {
            'field': form[fname], 'help_display_mode': 'tooltip'
        })
    return result


@register.simple_tag
def render_field_width(field):
    """."""
    form = field.form
    if hasattr(form, "field_widths") and field.name in form.field_widths:
        width = form.field_widths[field.name]
    else:
        width = 5
    return "col-lg-{0} col-md-{0} col-sm-{0}".format(width)
