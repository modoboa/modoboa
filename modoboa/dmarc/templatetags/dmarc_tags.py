"""Custom template tags."""

import datetime

from collections import OrderedDict

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.simple_tag
def next_period(period):
    """Return next period."""
    current = period.split("-")
    if int(current[1]) == 52:
        week0 = datetime.datetime.strptime(f"{int(current[0]) + 1}-0-1", "%Y-%W-%w")
        week1 = datetime.datetime.strptime(f"{int(current[0]) + 1}-1-1", "%Y-%W-%w")
        week52 = datetime.datetime.strptime(f"{current[0]}-52-1", "%Y-%W-%w")
        if week0 == week52 or week0 == week1:
            parts = (int(current[0]) + 1, 1)
        else:
            parts = (int(current[0]) + 1, 0)
    else:
        parts = (current[0], int(current[1]) + 1)
    return mark_safe(f"{parts[0]}-{parts[1]}")


@register.simple_tag
def previous_period(period):
    """Return previous period."""
    current = period.split("-")
    if int(current[1]) == 1:
        week0 = datetime.datetime.strptime(f"{current[0]}-0-1", "%Y-%W-%w")
        week1 = datetime.datetime.strptime(f"{current[0]}-1-1", "%Y-%W-%w")
        if week0 == week1:
            parts = (int(current[0]) - 1, 52)
        else:
            parts = (current[0], 0)
    elif int(current[1]) == 0:
        week0 = datetime.datetime.strptime(f"{current[0]}-0-1", "%Y-%W-%w")
        week52 = datetime.datetime.strptime(f"{int(current[0]) - 1}-52-1", "%Y-%W-%w")
        if week0 == week52:
            parts = (int(current[0]) - 1, 51)
        else:
            parts = (int(current[0]) - 1, 52)
    else:
        parts = (current[0], int(current[1]) - 1)
    return mark_safe(f"{parts[0]}-{parts[1]}")


@register.filter
def domain_sorted_items(domain_dict):
    """Return a list of tuples ordered alphabetically by domain names."""
    if isinstance(domain_dict, dict):
        sorted_domain_dict = OrderedDict(
            sorted(domain_dict.items(), key=lambda t: t[0])
        )
        unresolved_label = _("Not resolved")
        unresolved = sorted_domain_dict.pop(unresolved_label, None)
        if unresolved:
            sorted_domain_dict[unresolved_label] = unresolved
        return sorted_domain_dict.items()

    raise ValueError("domain_dict is not a dict")
