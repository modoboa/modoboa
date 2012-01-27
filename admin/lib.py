# coding: utf-8
from functools import wraps
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from models import *
from modoboa.lib.webutils import _render_error, _render
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
        kwargs["objects"] = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        kwargs["objects"] = paginator.page(paginator.num_pages)
    kwargs["last_page"] = paginator.num_pages
    kwargs["total"] = paginator.count
    kwargs["table"] = tblclass(request, kwargs["objects"].object_list)
    
    return _render(request, tplname, kwargs)

def grant_access_to_object(user, obj, is_owner=False):
    """Grant access to an object for a given user

    There are two different cases where we want to grant access to an
    object for a specific user:

    * He is the owner (he's just created the object)
    * He is going to administrate the object (but he is not the owner)

    :param user: a ``User`` object
    :param obj: an admin. object (Domain, Mailbox, ...)
    :param is_owner: the user is the unique object's owner
    """
    try:
        ct = ContentType.objects.get_for_model(obj)
        entry = user.objectaccess_set.get(content_type=ct, object_id=obj.id)
        entry.is_owner = is_owner
        entry.save()
    except ObjectAccess.DoesNotExist:
        pass
    else:
        return

    try:
        objaccess = ObjectAccess(user=user, content_object=obj, is_owner=is_owner)
        objaccess.save()
    except IntegrityError, e:
        raise AdminError(_("Failed to grant access (%s)" % str(e)))

def ungrant_access_to_object(obj, user=None):
    """Ungrant access to an object for a specific user

    If no user is provided, all entries referencing this object are
    deleted from the database.

    :param obj: an object inheriting from ``models.Model``
    :param user: a ``User`` object
    """
    ct = ContentType.objects.get_for_model(obj)
    if user:
        try:
            ObjectAccess.objects.get(user=user, content_type=ct, object_id=obj.id).delete()
        except ObjectAccess.DoesNotExist:
            pass
    else:
        ObjectAccess.objects.filter(content_type=ct, object_id=obj.id).delete()

def get_object_owner(obj):
    """Return the unique owner of this object

    :param obj: an object inheriting from ``model.Model``
    :return: a ``User`` object
    """
    ct = ContentType.objects.get_for_model(obj)
    try:
        entry = ObjectAccess.objects.get(content_type=ct, object_id=obj.id, is_owner=True)
    except ObjectAccess.DoesNotExist:
        return None
    return entry.user

def check_domain_access(f):
    """Decorator to check if the current user can access a domain

    This decorator only applies to url that contain a 'domid' or
    'mbid' parameter. (for a direct access)

    Raise a ``PermDeniedError`` if the current user can't view the
    requested object.
    """
    @wraps(f)
    def dec(request, **kwargs):
        if not request.user.is_superuser:
            domain = None
            domid = request.GET.get("domid", None)
            if domid:
                domain = Domain.objects.get(pk=domid)
            else:
                mbid = request.GET.get("mbid", None)
                if mbid:
                    domain = Mailbox.objects.get(pk=mbid).domain
            if domain and not request.user.can_access(domain):
                raise PermDeniedError(_("You can't access this domain"))

        return f(request, **kwargs)
    return dec
