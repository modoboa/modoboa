# coding: utf-8
import os
from django.conf import settings
from django import template
from django.contrib import messages
from django.template import Template, Context
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib import events
from modoboa.lib.sysutils import exec_cmd
from modoboa.lib.webutils import static_url

register = template.Library()

@register.simple_tag
def get_version():
    if os.path.isdir("%s/.hg" % settings.MODOBOA_DIR):
        version = "dev-"
        code, output = exec_cmd("hg id -i", cwd=settings.MODOBOA_DIR)
        version += output.rstrip()
        return version
    elif os.path.exists("%s/VERSION" % settings.MODOBOA_DIR):
        code, output = exec_cmd("cat %s/VERSION" % settings.MODOBOA_DIR)
        return output.rstrip()
    else:
        return "Unknown"

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
    return "[%s]" % ",".join(map(lambda v: '"%s"' % v, values))

@register.simple_tag
def display_messages(msgs):
    from django.contrib import messages

    text = ""
    level = "info"
    for m in msgs:
        level = m.tags
        text += unicode(m) + "\\\n"

    if level == "info":
        level = "success"
        timeout = "2000"
    else:
        timeout = "undefined"

    return """
<script type="text/javascript">
    $(document).ready(function() {
        $('body').notify('%s', '%s', %s);
    });
</script>
""" % (level, text, timeout)

@register.simple_tag
def extra_head_content(user):
    tpl = Template("{% for sc in static_content %}{{ sc|safe }}{% endfor %}")
    return tpl.render(
        Context(
            dict(static_content=events.raiseQueryEvent("GetStaticContent", user))
            )
        )

@register.simple_tag
def load_optionalmenu(user):
    menu = events.raiseQueryEvent("UserMenuDisplay", "top_menu_middle", user)
    return template.loader.render_to_string('common/menulist.html', 
                                            {"entries" : menu, "user" : user})

@register.simple_tag
def load_notifications(user):
    content = events.raiseQueryEvent("TopNotifications", user)
    return "".join(content)

@register.simple_tag
def render_form(form, tpl=None):
    if tpl is not None:
        return render_to_string(tpl, dict(form=form))

    ret = ""
    for field in form:
        ret += "%s\n" % render_field(field)
    return ret

@register.simple_tag
def render_field(field):
    return render_to_string("common/generic_field.html", dict(
            field=field
            ))

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
        if not form.fields.has_key(fname):
            break
        bfield = forms.BoundField(form, form.fields[fname], fname)
        if len(bfield.errors):
            haserror = True
        group += [bfield]
        cpt += 1

    return render_to_string("common/generic_fields_group.html", dict(
            label=label, group=group, haserror=haserror
            ))

@register.simple_tag
def pagination_bar(page):
    return render_to_string("common/pagination_bar.html", dict(
            page=page
            ))

@register.simple_tag
def alert(msg, typ):
    t = Template("""<div class="alert alert-{{ type }}">
<a class="close" data-dismiss="alert">×</a>
{{ msg }}
</div>""")
    return t.render(Context(dict(type=typ, msg=msg)))

@register.simple_tag
def render_link(linkdef, mdclass=None):
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
