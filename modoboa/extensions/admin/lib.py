# coding: utf-8
from functools import wraps
from itertools import chain
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from modoboa.core.models import User
from modoboa.lib import events
from modoboa.lib.exceptions import PermDeniedException
from modoboa.lib.emailutils import split_mailbox
from modoboa.extensions.admin.models import (
    Domain, Alias
)


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
            raise PermDeniedException(_("A mailbox is required"))
        return wrapped_f
    return decorator


def get_identities(user, searchquery=None, idtfilter=None, grpfilter=None):
    """Return all the identities owned by a user.

    :param user: the desired user
    :param str searchquery: search pattern
    :param list idtfilter: identity type filters
    :param list grpfilter: group names filters
    :return: a queryset
    """
    accounts = []
    if idtfilter is None or not idtfilter or idtfilter == "account":
        ids = user.objectaccess_set \
            .filter(content_type=ContentType.objects.get_for_model(user)) \
            .values_list('object_id', flat=True)
        q = Q(pk__in=ids)
        if searchquery is not None:
            q &= Q(username__icontains=searchquery) \
                | Q(email__icontains=searchquery)
        if grpfilter is not None and grpfilter:
            if grpfilter == "SuperAdmins":
                q &= Q(is_superuser=True)
            else:
                q &= Q(groups__name=grpfilter)
        accounts = User.objects.select_related().filter(q)

    aliases = []
    if idtfilter is None or not idtfilter \
            or (idtfilter in ["alias", "forward", "dlist"]):
        alct = ContentType.objects.get_for_model(Alias)
        ids = user.objectaccess_set.filter(content_type=alct) \
            .values_list('object_id', flat=True)
        q = Q(pk__in=ids)
        if searchquery is not None:
            if '@' in searchquery:
                local_part, domname = split_mailbox(searchquery)
                if local_part:
                    q &= Q(address__icontains=local_part)
                if domname:
                    q &= Q(domain__name__icontains=domname)
            else:
                q &= Q(address__icontains=searchquery) | \
                    Q(domain__name__icontains=searchquery)
        aliases = Alias.objects.select_related().filter(q)
        if idtfilter is not None and idtfilter:
            aliases = [al for al in aliases if al.type == idtfilter]
    return chain(accounts, aliases)


def get_domains(user, domfilter=None, searchquery=None, **extrafilters):
    """Return all the domains the user can access.

    :param ``User`` user: user object
    :param str searchquery: filter
    :rtype: list
    :return: a list of domains and/or relay domains
    """
    domains = []
    if domfilter is None or not domfilter or domfilter == 'domain':
        domains = Domain.objects.get_for_admin(user)
        if searchquery is not None:
            q = Q(name__contains=searchquery)
            q |= Q(domainalias__name__contains=searchquery)
            domains = domains.filter(q).distinct()
    extra_domain_entries = events.raiseQueryEvent(
        'ExtraDomainEntries', user, domfilter, searchquery, **extrafilters
    )
    return chain(domains, extra_domain_entries)


def check_if_domain_exists(name, extra_checks=None):
    """Check if a domain already exists.

    We not only look for domains, we also look for every object that
    could conflict with a domain (domain alias, etc.)

    """
    dtypes = events.raiseQueryEvent('CheckDomainName')
    if extra_checks is not None:
        dtypes = extra_checks + dtypes
    for dtype, label in dtypes:
        if dtype.objects.filter(name=name).exists():
            return label
    return None
