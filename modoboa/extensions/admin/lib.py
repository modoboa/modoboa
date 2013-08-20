# coding: utf-8
from functools import wraps
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.contenttypes.models import ContentType
from modoboa.core.models import User
from modoboa.lib import parameters
from modoboa.lib.exceptions import ModoboaException
from modoboa.lib.emailutils import split_mailbox
from modoboa.extensions.admin.models import Alias


def needs_mailbox():
    """Check if the current user owns at least one mailbox

    Some applications (the webmail for example) need a mailbox to
    work.
    """
    def decorator(f):
        @wraps(f)
        def wrapped_f(request, *args, **kwargs):
            if request.user.mailbox_set.count():
                return f(request, *args, **kwargs)
            raise ModoboaException()
        return wrapped_f
    return decorator


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
    paginator = Paginator(
        objects, int(parameters.get_admin("ITEMS_PER_PAGE", app="core"))
    )
    try:
        page = paginator.page(int(pagenum))
    except (EmptyPage, PageNotAnInteger, ValueError):
        page = paginator.page(paginator.num_pages)
    return page


def get_identities(user, args=None):
    """Return all the identities owned by a user

    :param user: the desired user
    :param args: a args object
    :return: a queryset
    """
    from itertools import chain

    if args:
        squery = args.get("searchquery", None)
        idtfilter = args.getlist("idtfilter", None)
        grpfilter = args.getlist("grpfilter", None)
    else:
        squery = None
        idtfilter = None
        grpfilter = None

    accounts = []
    if not idtfilter or "account" in idtfilter:
        ids = user.objectaccess_set \
            .filter(content_type=ContentType.objects.get_for_model(user)) \
            .values_list('object_id', flat=True)
        q = Q(pk__in=ids)
        if squery:
            q &= Q(username__icontains=squery) | Q(email__icontains=squery)
        if grpfilter and len(grpfilter):
            if "SuperAdmins" in grpfilter:
                q &= Q(is_superuser=True)
                grpfilter.remove("SuperAdmins")
                if len(grpfilter):
                    q |= Q(groups__name__in=grpfilter)
            else:
                q &= Q(groups__name__in=grpfilter)
        accounts = User.objects.select_related().filter(q)

    aliases = []
    if not idtfilter or ("alias" in idtfilter
                         or "forward" in idtfilter
                         or "dlist" in idtfilter):
        alct = ContentType.objects.get_for_model(Alias)
        ids = user.objectaccess_set.filter(content_type=alct) \
            .values_list('object_id', flat=True)
        q = Q(pk__in=ids)
        if squery:
            if '@' in squery:
                local_part, domname = split_mailbox(squery)
                if local_part:
                    q &= Q(address__icontains=local_part)
                if domname:
                    q &= Q(domain__name__icontains=domname)
            else:
                q &= Q(address__icontains=squery) | Q(domain__name__icontains=squery)
        aliases = Alias.objects.select_related().filter(q)
        if idtfilter:
            aliases = [al for al in aliases if al.type in idtfilter]

    return chain(accounts, aliases)
