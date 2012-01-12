# coding: utf-8
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from models import *
from modoboa.lib.webutils import _render_error, _render
from modoboa.admin.tables import *

def is_not_localadmin(errortpl="error"):
    def dec(f):
        def wrapped_f(request, *args, **kwargs):
            if request.user.id == 1:
                return _render_error(request, errortpl, {
                        "error" : _("Invalid action, %(user)s is a local user" \
                                        % {"user" : request.user.username})
                        })
            return f(request, *args, **kwargs)

        wrapped_f.__name__ = f.__name__
        wrapped_f.__dict__ = f.__dict__
        wrapped_f.__doc__ = f.__doc__
        wrapped_f.__module__ = f.__module__
        return wrapped_f
    return dec

def is_domain_admin(user):
    """Tell if a user is administrator for a domain of not

    Whatever the domain, we just want to know if the given user is
    declared as a domain administrator.

    :param user: a User object
    :return: True if the user is a domain administrator, False otherwise.
    """
    grp = Group.objects.get(name="DomainAdmins")
    return grp in user.groups.all()

def good_domain(f):
    """Custom permission decorator

    Check if a domain administrator is accessing the good domain.

    :param f: the original called function
    """
    def dec(request, **kwargs):
        if request.user.is_superuser:
            return f(request, **kwargs)
        if is_domain_admin(request.user):
            mb = Mailbox.objects.get(user=request.user.id)
            access = True
            if request.GET.has_key("domid"):
                dom_id = int(request.GET["domid"])
                if dom_id != mb.domain.id:
                    access = False
            else:
                q = request.GET.copy()
                q["domid"] = mb.domain.id
                request.GET = q
            if access:
                return f(request, **kwargs)

        from django.conf import settings
        from django.utils.http import urlquote
        path = urlquote(request.get_full_path())
        login_url = settings.LOGIN_URL
        return HttpResponseRedirect("%s?next=%s" % (login_url, path))
    return dec

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
        kwargs["objects"] = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        kwargs["objects"] = paginator.page(paginator.num_pages)
    kwargs["last_page"] = paginator.num_pages
    kwargs["total"] = paginator.count
    kwargs["table"] = tblclass(request, kwargs["objects"].object_list)
    
    return _render(request, tplname, kwargs)
