from django import template
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from modoboa.lib.webutils import render_actions
from modoboa.lib.templatetags.form_tags import configure_field_classes

register = template.Library()


@register.simple_tag
def sfilters_menu(user):
    entries = [
        {"name": "newfilterset",
         "img": "glyphicon glyphicon-plus",
         "label": _("New filters set"),
         "url": reverse("modoboa.extensions.sievefilters.views.new_filters_set"),
         "modal": True,
         "modalcb": "filtersetform_cb"
         }
    ]

    return render_to_string('common/menulist.html',
                            {"entries": entries, "user": user})


@register.simple_tag
def fset_menu(mode, setname):
    entries = []
    if mode == "gui":
        entries += [
            {"name": "newfilter",
             "img": "glyphicon glyphicon-plus",
             "label": _("New filter"),
             "url": reverse("modoboa.extensions.sievefilters.views.newfilter",
                             args=[setname]),
             "modal": True,
             "autowidth": True,
             "modalcb": "filterform_cb"}
        ]
    if mode == "raw":
        entries += [
            {"name": "savefs",
             "img": "glyphicon glyphicon-download-alt",
             "label": _("Save filters set"),
             "url": reverse("modoboa.extensions.sievefilters.views.savefs",
                             args=[setname])},
        ]

    entries += [
        {"name": "activatefs",
         "img": "glyphicon glyphicon-ok",
         "label": _("Activate filters set"),
         "url": reverse("modoboa.extensions.sievefilters.views.activate_filters_set",
                         args=[setname])},
        {"name": "removefs",
         "img": "glyphicon glyphicon-trash",
         "label": _("Remove filters set"),
         "url": reverse("modoboa.extensions.sievefilters.views.remove_filters_set",
                         args=[setname])},
        {"name": "downloadfs",
         "img": "glyphicon glyphicon-download",
         "label": _("Download"),
         "url": reverse("modoboa.extensions.sievefilters.views.download_filters_set",
                         args=[setname])}
    ]

    return render_to_string('common/menulist.html',
                            {"entries": entries})


@register.simple_tag
def filter_actions(setname, f, position, islast):
    actions = [
        {"name": "editfilter",
         "url": reverse("modoboa.extensions.sievefilters.views.editfilter",
                         args=[setname, f["name"]]),
         "img": "glyphicon glyphicon-edit",
         "title": _("Edit filter"),
         "modal": True,
         "autowidth": True,
         "modalcb": "filterform_cb"},
        {"name": "removefilter",
         "url": reverse("modoboa.extensions.sievefilters.views.removefilter",
                         args=[setname, f["name"]]),
         "img": "glyphicon glyphicon-trash",
         "title": _("Remove this filter")}
    ]
    if position != 1:
        actions += [
            {"name": "movefilter_up",
             "url": reverse("modoboa.extensions.sievefilters.views.move_filter_up",
                             args=[setname, f["name"]]),
             "img": "glyphicon glyphicon-arrow-up",
             "title": _("Move this filter up")}
        ]
    if not islast:
        actions += [
            {"name": "movefilter_down",
             "url": reverse("modoboa.extensions.sievefilters.views.move_filter_down",
                             args=[setname, f["name"]]),
             "img": "glyphicon glyphicon-arrow-down",
             "title": _("Move this filter down")},
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
        "errors": errors
    }))


@register.simple_tag
def display_condition(form, cnt):
    target = form["cond_target_%d" % cnt]
    configure_field_classes(target)
    operator = form["cond_operator_%d" % cnt]
    configure_field_classes(operator)
    value = form["cond_value_%d" % cnt]
    configure_field_classes(value)
    t = template.Template("""
<div id="condition_{{ idx }}" class="item">
  <div class="col-lg-3 col-md-3 col-sm-3">{{ tfield }}</div>
  <div class="col-lg-3 col-md-3 col-sm-3">{{ofield}}</div>
  <div class="col-lg-4 col-md-4 col-sm-4">{{ vfield }}</div>
  {{ verrors }}
</div>
""")
    return t.render(template.Context({
        "idx": cnt,
        "tfield": target,
        "ofield": operator,
        "vfield": value,
        "verrors": display_errors(value.errors)
    }))


@register.simple_tag
def display_action(form, cnt):
    action = form["action_name_%d" % cnt]
    configure_field_classes(action)
    values = []
    acnt = 0
    verrors = []
    while True:
        try:
            field = form["action_arg_%d_%d" % (cnt, acnt)]
            configure_field_classes(field)
            values += [field]
            if field.errors:
                verrors += field.errors
            acnt += 1
        except KeyError:
            break
    t = template.Template("""
<div id="action_{{ idx }}" class="item">
<div class="col-lg-5 col-md-5 col-sm-5">
  {{ afield }}
  </div>
  {% for v in values %}
    <div class="col-lg-5 col-md-5 col-sm-5">{{ v }}</div>
  {% endfor %}{{ verrors }}
</div>
""")
    return t.render(template.Context({
        "idx": cnt,
        "afield": action, "values": values,
        "verrors": display_errors(verrors)
    }))
