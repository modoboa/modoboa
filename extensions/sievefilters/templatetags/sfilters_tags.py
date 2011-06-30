from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from modoboa.extensions.sievefilters import views
from modoboa.lib import render_actions

register = template.Library()

from modoboa.lib import static_url

@register.simple_tag
def sfilters_menu(user):
    entries = [
        {"name"  : "newfilterset",
         "img"   : static_url("pics/add.png"),
         "label" : _("New filters set"),
         "url" : reverse(views.new_filters_set),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:300,y:170}}"
         }
        ]

    return render_to_string('common/menulist.html', 
                            {"entries" : entries, "user" : user})

@register.simple_tag
def fset_menu(mode, setname):
    entries = []
    if mode == "gui":
        entries += [
            {"name" : "newfilter",
             "img" : static_url("pics/add.png"),
             "label" : _("New filter"),
             "url" : reverse(views.newfilter, args=[setname]),
             "class" : "boxed",
             "rel" : "{handler:'iframe',size:{x:700,y:400}}"},

            ]
    if mode == "raw":
        entries += [
            {"name" : "savefs",
             "img" : static_url("pics/save.png"),
             "label" : _("Save filters set"),
             "url" : reverse(views.savefs, args=[setname])},
            ]

    entries += [
        {"name" : "activatefs",
         "img" : static_url("pics/active.png"),
         "label" : _("Activate filters set"),
         "url" : reverse(views.activate_filters_set, args=[setname])},
        {"name" : "removefs",
         "img" : static_url("pics/remove.png"),
         "label" : _("Remove filters set"),
         "url" : reverse(views.remove_filters_set, args=[setname])},
        {"name" : "downloadfs",
         "img" : static_url("pics/download.png"),
         "label" : _("Download"),
         "url" : reverse(views.download_filters_set, args=[setname])}
        ]

    return render_to_string('common/menu.html', 
                            {"entries" : entries})

@register.simple_tag
def filter_actions(setname, f, position, islast):
    actions = [
        {"name" : "editfilter",
         "url" : reverse(views.editfilter, args=[setname, f["name"]]),
         "img" : static_url("pics/edit.png"),
         "title" : _("Edit filter"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:650,y:400}}"},
        {"name" : "removefilter",
         "url" : reverse(views.removefilter, args=[setname, f["name"]]),
         "img" : static_url("pics/remove.png"),
         "title" : _("Remove this filter")}
        ]
    if position != 1:
        actions += [
            {"name" : "movefilter_up",
             "url" : reverse(views.move_filter_up, args=[setname, f["name"]]),
             "img" : static_url("pics/moveup.png"),
             "title" : _("Move this filter up")}
            ]
    if not islast:
        actions += [
            {"name" : "movefilter_down",
             "url" : reverse(views.move_filter_down, args=[setname, f["name"]]),
             "img" : static_url("pics/movedown.png"),
             "title" : _("Move this filter down")},
            ]
    return render_actions(actions)

@register.simple_tag
def display_errors(errors):
    if not len(errors):
        return ""
    t = template.Template("""
<ul class="errors">
  {% for error in errors %}
  <li>{{ error|safe }}</li>
  {% endfor %}
</ul>
""")
    return t.render(template.Context({
                "errors" : errors
                }))

@register.simple_tag
def display_condition(form, cnt):
    target = form["cond_target_%d" % cnt]
    operator = form["cond_operator_%d" % cnt]
    value = form["cond_value_%d" % cnt]
    t = template.Template("""
<div class="item">
  {{ tfield }}{{ofield}}{{ vfield }}{{ verrors }}
</div>
""")
    return t.render(template.Context({
                "tfield" : target,
                "ofield" : operator, 
                "vfield" : value,
                "verrors" : display_errors(value.errors)
                }))

@register.simple_tag
def display_action(form, cnt):
    action = form["action_name_%d" % cnt]
    values = []
    acnt = 0
    verrors = []
    while True:
        try:
            values += [form["action_arg_%d_%d" % (cnt, acnt)]]
            if len(form["action_arg_%d_%d" % (cnt, acnt)].errors):
                verrors += form["action_arg_%d_%d" % (cnt, acnt)].errors
            acnt += 1
        except KeyError:
            break
    t = template.Template("""
<div class="item">
  {{ afield }}{% for v in values %}{{ v }}{% endfor %}{{ verrors }}
</div>
""")
    return t.render(template.Context({
                "afield" : action, "values" : values, 
                "verrors" : display_errors(verrors)
                }))
