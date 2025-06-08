"""
Form rendering tags.
"""

from django import forms, template
from django.template.loader import render_to_string

register = template.Library()


def configure_field_classes(field):
    """Add required CSS classes to field."""
    if isinstance(field.field.widget, forms.CheckboxInput) or isinstance(
        field.field.widget, forms.RadioSelect
    ):
        return
    if "class" in field.field.widget.attrs:
        field.field.widget.attrs["class"] += " form-control"
    else:
        field.field.widget.attrs["class"] = "form-control"


@register.simple_tag
def render_field(field, help_display_mode="tooltip", label_width="col-sm-4", **options):
    """Render a field."""
    configure_field_classes(field)
    context = {
        "field": field,
        "help_display_mode": help_display_mode,
        "label_width": label_width,
        "deactivate_if_empty": True,
    }
    context.update(options)
    return render_to_string("common/generic_field.html", context)


@register.simple_tag
def render_field_width(field):
    """."""
    form = field.form
    if hasattr(form, "field_widths") and field.name in form.field_widths:
        width = form.field_widths[field.name]
    else:
        width = 5
    return f"col-sm-{width}"
