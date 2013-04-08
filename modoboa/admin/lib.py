# coding: utf-8
from django.utils.translation import ugettext as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from modoboa.lib.webutils import ajax_simple_response
from modoboa.lib import parameters
from modoboa.lib.templatetags.libextras import pagination_bar
from modoboa.admin.tables import *
from exceptions import *

def render_listing(request, objtype, **kwargs):
    """Common function to render a listing

    All listing pages available into the admin application use the
    same layout, rendered by this function.

    :param request: a ``Request`` object
    :param objtype: the object type's name (lowercase)
    """
    tblclass = "%sTable" % objtype.capitalize()
    if not globals().has_key(tblclass):
        raise AdminError(_("Unknown object type"))
    tblclass = globals()[tblclass]
    
    if request.GET.has_key("domid"):
        kwargs["domid"] = request.GET["domid"]
    else:
        kwargs["domid"] = ""
    paginator = Paginator(kwargs["objects"], 
                          int(parameters.get_admin("ITEMS_PER_PAGE")))
    try:
        pagenum = request.GET.get("page", "1")
    except ValueError:
        pagenum = 1
    try:
        page = paginator.page(pagenum)
    except (EmptyPage, PageNotAnInteger):
        page = paginator.page(paginator.num_pages)
    
    return ajax_simple_response({
        "table" : tblclass(request, page.object_list).render(),
        "page" : page.number,
        "paginbar" : pagination_bar(page),
        "handle_mailboxes": parameters.get_admin("HANDLE_MAILBOXES", 
                                                 raise_error=False),
        "auto_account_removal": parameters.get_admin("AUTO_ACCOUNT_REMOVAL")
    })
