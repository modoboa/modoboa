# coding: utf-8
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from modoboa.lib import parameters


def get_sort_order(qdict, default, allowed_values=None):
    """Return a sort order from a querydict object

    :param QueryDict qdict: the object to analyse
    :param string default: the default sort order if no one is found
    :param list allowed_values: an optional list of allowed values
    :return: a 2uple of strings
    """
    sort_order = qdict.get("sort_order", default)
    if sort_order.startswith("-"):
        sort_dir = "-"
        sort_order = sort_order[1:]
    else:
        sort_dir = ""
    if allowed_values is not None and not sort_order in allowed_values:
        return (default, "")
    return (sort_order, sort_dir)


def get_listing_page(objects, pagenum):
    paginator = Paginator(objects, int(parameters.get_admin("ITEMS_PER_PAGE")))
    try:
        page = paginator.page(int(pagenum))
    except (EmptyPage, PageNotAnInteger, ValueError):
        page = paginator.page(paginator.num_pages)
    return page
