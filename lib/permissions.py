# coding: utf-8
from functools import wraps
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from modoboa.admin.models import ObjectAccess
import events

def get_content_type(obj):
    """Simple function that use the right method to retrieve a content type

    :param obj: a django model
    :return: a ``ContentType`` object
    """
    return obj.get_content_type() if hasattr(obj, "get_content_type") \
        else ContentType.objects.get_for_model(obj)

def get_account_roles(user):
    """Return the list of supported account roles
    
    This list can be extended by extensions which listen to the
    ``GetExtraRoles`` event.

    :return: list of strings
    """
    std_roles = [("SimpleUsers", _("Simple user"))]
    if user.is_superuser:
        std_roles += [("SuperAdmins",  _("Super administrator"))]
    if user.has_perm("admin.add_domain"):
        std_roles += [("DomainAdmins", _("Domain administrator"))]
    std_roles += events.raiseQueryEvent("GetExtraRoles", user)
    return sorted(std_roles, key=lambda role: role[1])

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
    ct = get_content_type(obj)
    try:
        entry = user.objectaccess_set.get(content_type=ct, object_id=obj.id)
        entry.is_owner = is_owner
        entry.save()
    except ObjectAccess.DoesNotExist:
        pass
    else:
        return

    try:
        objaccess = ObjectAccess(user=user, content_type=ct, 
                                 object_id=obj.id, is_owner=is_owner)
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
    ct = get_content_type(obj)
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
    ct = get_content_type(obj)
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
