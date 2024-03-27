"""Custom template tags."""

from django import template
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from modoboa.lib.web_utils import render_actions
from modoboa.lib.templatetags.form_tags import configure_field_classes

from .. import lib

register = template.Library()


@register.simple_tag
def sfilters_menu(user):
    entries = [
        {
            "name": "newfilterset",
            "img": "fa fa-plus",
            "label": _("New filters set"),
            "url": reverse("sievefilters:fs_add"),
            "modal": True,
            "modalcb": "filtersetform_cb",
        }
    ]

    return render_to_string("common/menulist.html", {"entries": entries, "user": user})


@register.simple_tag
def fset_menu(mode, setname):
    entries = []
    if mode == "gui":
        entries += [
            {
                "name": "newfilter",
                "img": "fa fa-plus",
                "label": _("New filter"),
                "url": reverse("sievefilters:filter_add", args=[setname]),
                "modal": True,
                "autowidth": True,
                "modalcb": "filterform_cb",
            }
        ]
    if mode == "raw":
        entries += [
            {
                "name": "savefs",
                "img": "fa fa-download-alt",
                "label": _("Save filters set"),
                "url": reverse("sievefilters:fs_save", args=[setname]),
            },
        ]

    entries += [
        {
            "name": "activatefs",
            "img": "fa fa-check",
            "label": _("Activate filters set"),
            "url": reverse("sievefilters:fs_activate", args=[setname]),
        },
        {
            "name": "removefs",
            "img": "fa fa-trash",
            "label": _("Remove filters set"),
            "url": reverse("sievefilters:fs_delete", args=[setname]),
        },
        {
            "name": "downloadfs",
            "img": "fa fa-download",
            "label": _("Download"),
            "url": reverse("sievefilters:fs_download", args=[setname]),
        },
    ]

    return render_to_string("common/menulist.html", {"entries": entries})


@register.simple_tag
def filter_actions(setname, f, position, islast):
    actions = [
        {
            "name": "editfilter",
            "url": reverse("sievefilters:filter_change", args=[setname, f["name"]]),
            "img": "fa fa-edit",
            "title": _("Edit filter"),
            "modal": True,
            "autowidth": True,
            "modalcb": "filterform_cb",
        },
        {
            "name": "removefilter",
            "url": reverse("sievefilters:filter_delete", args=[setname, f["name"]]),
            "img": "fa fa-trash",
            "title": _("Remove this filter"),
        },
    ]
    if position != 1:
        actions += [
            {
                "name": "movefilter_up",
                "url": reverse(
                    "sievefilters:filter_move_up", args=[setname, f["name"]]
                ),
                "img": "fa fa-chevron-up",
                "title": _("Move this filter up"),
            }
        ]
    if not islast:
        actions += [
            {
                "name": "movefilter_down",
                "url": reverse(
                    "sievefilters:filter_move_down", args=[setname, f["name"]]
                ),
                "img": "fa fa-chevron-down",
                "title": _("Move this filter down"),
            },
        ]
    return render_actions(actions)


@register.simple_tag
def display_errors(errors):
    if not len(errors):
        return ""
    t = template.Template(
        """
<ul class="errors">
  {% for error in errors %}
  <li>{{ error|safe }}</li>
  {% endfor %}
</ul>
"""
    )
    return t.render(template.Context({"errors": errors}))


@register.simple_tag
def display_condition(form, cnt):
    target = form["cond_target_%d" % cnt]
    configure_field_classes(target)
    operator = form["cond_operator_%d" % cnt]
    configure_field_classes(operator)
    value = form["cond_value_%d" % cnt]
    configure_field_classes(value)
    t = template.Template(
        """
<div id="condition_{{ idx }}" class="item">
  <div class="col-lg-3 col-md-3 col-sm-3">{{ tfield }}</div>
  <div class="col-lg-3 col-md-3 col-sm-3">{{ofield}}</div>
  <div class="col-lg-4 col-md-4 col-sm-4">{{ vfield }}</div>
  {{ verrors }}
</div>
"""
    )
    return t.render(
        template.Context(
            {
                "idx": cnt,
                "tfield": target,
                "ofield": operator,
                "vfield": value,
                "verrors": display_errors(value.errors),
            }
        )
    )


@register.simple_tag
def display_action(form, cnt):
    action = form["action_name_%d" % cnt]
    tpl = lib.find_action_template(action.initial)
    configure_field_classes(action)
    values = []
    verrors = []
    for pos, argtpl in enumerate(tpl.get("args", [])):
        fieldname = "action_arg_{}_{}".format(cnt, pos)
        if fieldname not in form.fields:
            continue
        field = form[fieldname]
        configure_field_classes(field)
        arg = {"field": field}
        if field.errors:
            verrors += field.errors
        if argtpl["type"] == "boolean":
            arg["checkbox"] = True
        values += [arg]
    t = template.Template(
        """
<div id="action_{{ idx }}" class="item">
<div class="col-sm-4">
  {{ afield }}
  </div>
  <div class="col-sm-6">
  {% for v in values %}{% if v.checkbox %}<div class="checkbox"><label>{{ v.field }} {{ v.field.label }}</label></div>{% else %}{{ v.field }}{% endif %}{% endfor %}
  {{ verrors }}
  </div>
</div>
"""
    )
    return t.render(
        template.Context(
            {
                "idx": cnt,
                "afield": action,
                "values": values,
                "verrors": display_errors(verrors),
            }
        )
    )
