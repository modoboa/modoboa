from django import template
from django.utils.translation import ugettext as _

register = template.Library()

@register.simple_tag
def getLabel(var):
    labels = {
        "day" : _("Day"),
        "week" : _("Week"),
        "month" : _("Month"),
        "year" : _("Year")
        }
    return labels.has_key(var) and labels[var] or var
