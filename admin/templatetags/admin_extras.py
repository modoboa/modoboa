from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

register = template.Library()

genders = {
    "Enabled" : (_("enabled_m"), _("enabled_f"))
}

@register.simple_tag
def domain_menu(domain_id, selection):
    return render_to_string('admin/domain_menu.html', 
                            {"selection" : selection,
                             "domain_id" : domain_id})

@register.simple_tag
def settings_menu(selection):
    return render_to_string('admin/settings_menu.html',
                            {"selection" : selection})

@register.filter
def gender(value, target):
    if genders.has_key(value):
        return target == "m" and genders[value][0] or genders[value][1]
    return value
