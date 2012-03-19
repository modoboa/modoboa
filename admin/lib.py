# coding: utf-8
from django.utils.translation import ugettext as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from modoboa.lib.webutils import _render
from modoboa.lib import parameters
from modoboa.admin.tables import *
from exceptions import *

def render_listing(request, objtype, tplname="admin/listing.html",
                   **kwargs):
    """Common function to render a listing

    All listing pages available into the admin application use the
    same layout, rendered by this function.

    :param request: a ``Request`` object
    :param objtype: the object type's name (lowercase)
    :param tplname: the template used to render the HTML
    """
    tblclass = "%sTable" % objtype.capitalize()
    if not globals().has_key(tblclass):
        raise AdminError(_("Unknown object type"))
    tblclass = globals()[tblclass]
    
    if request.GET.has_key("domid"):
        kwargs["domid"] = request.GET["domid"]
    else:
        kwargs["domid"] = ""
    kwargs["selection"] = objtype
    paginator = Paginator(kwargs["objects"], 
                          int(parameters.get_admin("ITEMS_PER_PAGE")))
    try:
        page = request.GET.get("page", "1")
    except ValueError:
        page = 1
    try:
        kwargs["page"] = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        kwargs["page"] = paginator.page(paginator.num_pages)
    kwargs["table"] = tblclass(request, kwargs["page"].object_list)
    kwargs["selection"] = objtype
    
    return _render(request, tplname, kwargs)
