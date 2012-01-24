# coding: utf-8
from functools import wraps
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from models import *
from modoboa.lib.exceptions import ModoboaException
from modoboa.lib.webutils import _render_error, _render
from modoboa.admin.tables import *

class AdminError(ModoboaException):
    """
    Just a Custom exception to identify errors coming from the admin
    application.
    """
    pass

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

def set_object_ownership(user, obj):
    """Simple shorcut to associate an object to a user

    :param user: a ``User`` object
    :param obj: an admin. object (Domain, Mailbox, ...)
    """
    try:
        ct = ContentType.objects.get_for_model(obj)
        obj_owner = user.objectowner_set.get(content_type=ct, object_id=obj.id)
    except ObjectOwner.DoesNotExist:
        obj_owner = ObjectOwner(user=user, content_object=obj)
        obj_owner.save()

def unset_object_ownership(obj):
    """Remove the ownership of the given object

    :param obj: an object inheriting from ``models.Model``
    """
    ct = ContentType.objects.get_for_model(obj)
    ObjectOwner.objects.get(content_type=ct, object_id=obj.id).delete()

def is_object_owner(user, obj):
    """Check if a user is the object's owner

    An object can only belongs to one user. 

    This function is recursive : if the given user is not the owner
    and if he owns other ``User`` objects, we also check if one of
    those users owns the object.

    :param user: a ``User`` object
    :param obj: a admin object
    :return: a boolean
    """
    if user.is_superuser:
        return True

    ct = ContentType.objects.get_for_model(obj)
    try:
        ooentry = user.objectowner_set.get(content_type=ct, object_id=obj.id)
    except ObjectOwner.DoesNotExist:
        pass
    else:
        return True
    if ct.model == "user":
        return False

    ct = ContentType.objects.get_for_model(User)
    qs = user.objectowner_set.filter(content_type=ct)
    for ooentry in qs.all():
        if is_object_owner(ooentry.content_object, obj):
            return True
    return False

def get_object_owner(obj):
    """Return this object's owner

    :param obj: an object inheriting from ``model.Model``
    :return: a ``User`` object
    """
    ct = ContentType.objects.get_for_model(obj)
    res = ObjectOwner.objects.filter(content_type=ct, object_id=obj.id)
    if not len(res):
        return None
    return res[0].user

def check_domain_ownership(f):
    """Decorator to check if the current user can access to a domain

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
            if domain and not is_object_owner(request.user, domain):
                raise PermDeniedError(_("You can't access this domain"))

        return f(request, **kwargs)
    return dec

def get_user_domains(user):
    if user.is_superuser:
        return Domain.objects.all()

    domct = ContentType.objects.get_for_model(Domain)
    qs = user.objectowner_set.filter(content_type=domct)
    domains = []
    for entry in qs.all():
        domains += [entry.content_object]

    userct = ContentType.objects.get_for_model(User)
    qs = user.objectowner_set.filter(content_type=userct)
    for entry in qs:
        if not is_domain_admin(entry.content_object):
            continue
        domains += get_user_domains(entry.content_object)
    return domains

def get_user_domains_qs(user):
    """Return the domains belonging to this user

    The result is a ``QuerySet`` object, so this function can be used
    to fill ``ModelChoiceField`` objects.

    :param user: a ``User`` object
    """
    if user.is_superuser:
        return Domain.objects.all()
    result = Domain.objects.filter(owners__user=user)
    
    userct = ContentType.objects.get_for_model(User)
    for entry in user.objectowner_set.filter(content_type=userct):
        if not is_domain_admin(entry.content_object):
            continue
        result |= get_user_domains_qs(entry.content_object)
    return result

def get_user_domaliases(user):
    """Return the domain aliases that belong to this user

    The result will contain the domain aliases defined for each domain
    that user can see.

    :param user: a ``User`` object
    :return: a list of ``DomainAlias`` objects
    """
    if user.is_superuser:
        return DomainAlias.objects.all()
    domains = get_user_domains_qs(user)
    domaliases = []
    for dom in domains:
        domaliases += dom.domainalias_set.all()
    return domaliases

def get_user_mailboxes(user):
    """Return the mailboxes that belong to this user

    The result will contain the mailboxes defined for each domain that
    user can see.

    :param user: a ``User`` object
    :return: a list of ``Mailbox`` objects
    """
    if user.is_superuser:
        return Mailbox.objects.all()
    mboxes = []
    domains = get_user_domains_qs(user)
    for dom in domains:
        mboxes += dom.mailbox_set.all()
    return mboxes

def get_user_mbaliases(user):
    """Return the mailbox aliases that belong to this user

    The result will contain the mailbox aliases defined for each
    domain that user can see.

    :param user: a ``User`` object
    :return: a list of ``Alias`` objects
    """
    if user.is_superuser:
        return Alias.objects.all()
    domains = get_user_domains_qs(user)
    mbaliases = []
    for dom in domains:
        mbaliases += dom.alias_set.all()
    return mbaliases
