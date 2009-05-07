from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

register = template.Library()

@register.simple_tag
def menu(selection, perms):
    return render_to_string('main/menu.html', 
                            {"selection" : selection, "perms" : perms})
