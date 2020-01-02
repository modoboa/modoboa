from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from modoboa.parameters import tools as param_tools


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
    if allowed_values is not None and sort_order not in allowed_values:
        return (default, "")
    return (sort_order, sort_dir)


def get_listing_page(objects, pagenum):
    """Return specific a listing page.

    A page contains a limited number of elements (see
    ITEMS_PER_PAGE). If the given page number is wrong, the first page
    will be always returned.

    :param list objects: object list to paginate
    :param int pagenum: page number
    :return: a ``Page`` object
    """
    paginator = Paginator(
        objects,
        param_tools.get_global_parameter("items_per_page", app="core"),
        allow_empty_first_page=False
    )
    try:
        page = paginator.page(int(pagenum))
    except (EmptyPage, PageNotAnInteger, ValueError):
        page = None
    return page
