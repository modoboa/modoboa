"""Custom template tags."""

from datetime import datetime

from django import template
from django.template import Context, Template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from modoboa.core import signals as core_signals

register = template.Library()


@register.simple_tag
def join(items, sep=","):
    res = ""
    for k, v in list(items.items()):
        if res != "":
            res += sep
        res += "%s : '%s'" % (k, v)
    return res


@register.simple_tag
def tolist(values):
    return mark_safe("[%s]" % ",".join(['"%s"' % v for v in values]))


@register.simple_tag
def alert(msg, typ):
    t = Template("""<div class="alert alert-{{ type }}" role="alert">
<button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>
{{ msg }}
</div>""")  # NOQA:E501
    return t.render(Context({"type": typ, "msg": msg}))


@register.simple_tag
def render_link(linkdef, mdclass=""):
    t = Template("""<a href="{{ link.url }}" name="{{ link.name }}" title="{{ link.title }}"
{% if link.modal %}data-toggle="ajaxmodal{% if link.autowidth %}-autowidth{% endif %}"{% endif %}
{% if link.modalcb %}modalcb="{{ link.modalcb }}"{% endif %}
{% if link.closecb %}closecb="{{ link.closecb }}"{% endif %}
class="{{ mdclass }}{% if link.class %} {{ link.class }}{% endif %}"
{% if link.confirm %} onclick="return confirm('{{ link.confirm }}')"{% endif %}
{% for attr, value in link.extra_attributes.items %} {{ attr }}="{{ value }}"{% endfor %}
>
{% if link.img %}<i class="{{ link.img }}"></i>{% endif %}
{{ link.label }}</a>""")  # NOQA:E501
    return t.render(Context({"link": linkdef, "mdclass": mdclass}))


@register.simple_tag
def progress_color(value):
    value = int(value)
    if value < 50:
        return "progress-bar progress-bar-info"
    if value < 80:
        return "progress-bar progress-bar-warning"
    return "progress-bar progress-bar-danger"


@register.filter
def fromunix(value):
    return datetime.fromtimestamp(int(value))


@register.simple_tag
def render_tags(tags):
    t = Template("""{% for tag in tags %}
<span class="label label-{% if tag.color %}{{ tag.color }}{% else %}default{% endif %}">
  <a href="#" class="filter {{ tag.type }}" name="{{ tag.name }}">{{ tag.label }}</a>
</span>
{% endfor %}
""")  # NOQA:E501
    return t.render(Context({"tags": tags}))


@register.simple_tag
def extra_static_content(caller, st_type, user):
    """Get extra static content from extensions.

    :param str caller: the application (location) responsible for the call
    :param str st_type: content type (css or js)
    :param ``User`` user: connected user
    """
    tpl = template.Template(
        "{% for sc in static_content %}{{ sc|safe }}{% endfor %}"
    )
    static_content = core_signals.extra_static_content.send(
        sender="extra_static_content",
        caller=caller, st_type=st_type, user=user)
    static_content = [result[1] for result in static_content]
    return tpl.render(
        template.Context({"static_content": static_content})
    )


@register.filter(name="localize_header_name")
def localize_header_name(headername):
    """ Localizes the header names """
    names = {
        "From": _("From"),
        "To": _("To"),
        "Date": _("Date"),
        "Subject": _("Subject")
    }
    return names.get(headername, headername)
