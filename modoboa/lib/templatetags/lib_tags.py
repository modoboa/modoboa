# coding: utf-8
from datetime import datetime
from django import template
from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy
from modoboa.lib import events
from modoboa.lib.formutils import SeparatorField

register = template.Library()


@register.simple_tag
def join(items, sep=','):
    res = ""
    for k, v in items.iteritems():
        if res != "":
            res += sep
        res += "%s : '%s'" % (k, v)
    return res


@register.simple_tag
def tolist(values):
    return "[%s]" % ",".join(['"%s"' % v for v in values])


@register.simple_tag
def render_form(form, tpl=None):
    if tpl is not None:
        return render_to_string(tpl, dict(form=form))

    ret = ""
    for field in form:
        ret += "%s\n" % render_field(field)
    return ret


@register.simple_tag
def render_field(field, help_display_mode="tooltip"):
    from modoboa.core.templatetags.core_tags import visirule

    if type(field.form.fields[field.name]) is SeparatorField:
        return "<h5%s>%s</h5>" % (visirule(field), unicode(field.label))

    return render_to_string("common/generic_field.html", dict(
        field=field, help_display_mode=help_display_mode
    ))


@register.simple_tag
def render_field_appended(field, text):
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
    from django.forms import forms

    first = forms.BoundField(form, form.fields[pattern], pattern)
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
def pagination_bar(page):
    return render_to_string("common/pagination_bar.html", dict(
        page=page, baseurl="?"
    ))


@register.simple_tag
def alert(msg, typ):
    t = Template("""<div class="alert alert-{{ type }}">
<a class="btn btn-default close" data-dismiss="alert">×</a>
{{ msg }}
</div>""")
    return t.render(Context(dict(type=typ, msg=msg)))


@register.simple_tag
def render_link(linkdef, mdclass=""):
    t = Template("""<a href="{{ link.url }}" name="{{ link.name }}" title="{{ link.title }}"
{% if link.modal %}data-toggle="ajaxmodal{% if link.autowidth %}-autowidth{% endif %}"{% endif %}
{% if link.modalcb %}modalcb="{{ link.modalcb }}"{% endif %}
{% if link.closecb %}closecb="{{ link.closecb }}"{% endif %}
class="{{ mdclass }}{% if link.class %} {{ link.class }}{% endif %}"
{% if link.confirm %} onclick="return confirm('{{ link.confirm }}')"{% endif %}>
{% if link.img %}<i class="{{ link.img }}"></i>{% endif %}
{{ link.label }}</a>""")
    return t.render(Context(dict(link=linkdef, mdclass=mdclass)))


@register.simple_tag
def progress_color(value):
    value = int(value)
    if value < 50:
        return "progress-success"
    if value < 80:
        return "progress-warning"
    return "progress-danger"


@register.filter
def fromunix(value):
    return datetime.fromtimestamp(int(value))


@register.simple_tag
def render_tags(tags):
    t = Template("""{% for tag in tags %}
<span class="label{% if tag.color %} label-{{ tag.color }}{% endif %}">
  <a href="#" class="filter {{ tag.type }}" name="{{ tag.name }}">{{ tag.label }}</a>
</span>
{% endfor %}
""")
    return t.render(Context({"tags": tags}))


@register.simple_tag
def extra_static_content(caller, user):
    """Get extra static content from extensions.

    :param str caller: the application (location) responsible for the call
    :param ``User`` user: connected user
    """
    tpl = template.Template(
        "{% for sc in static_content %}{{ sc|safe }}{% endfor %}"
    )
    return tpl.render(
        template.Context({
            'static_content': events.raiseQueryEvent("GetStaticContent", caller, user)
        })
    )
