# coding: utf-8

"""Internal library for admin."""

from functools import wraps
from itertools import chain

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.translation import ugettext as _

from modoboa.core.models import User
from modoboa.core import signals as core_signals
from modoboa.lib import events
from modoboa.lib.exceptions import PermDeniedException

from .models import Domain, DomainAlias, Alias


def needs_mailbox():
    """Check if the current user owns at least one mailbox

    Some applications (the webmail for example) need a mailbox to
    work.
    """
    def decorator(f):
        @wraps(f)
        def wrapped_f(request, *args, **kwargs):
            if hasattr(request.user, "mailbox"):
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
        accounts = User.objects.filter(q).prefetch_related("groups")

    aliases = []
    if idtfilter is None or not idtfilter \
            or (idtfilter in ["alias", "forward", "dlist"]):
        alct = ContentType.objects.get_for_model(Alias)
        ids = user.objectaccess_set.filter(content_type=alct) \
            .values_list('object_id', flat=True)
        q = Q(pk__in=ids, internal=False)
        if searchquery is not None:
            q &= (
                Q(address__icontains=searchquery) |
                Q(domain__name__icontains=searchquery)
            )
        aliases = Alias.objects.select_related("domain").filter(q)
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
    domains = (
        Domain.objects.get_for_admin(user).prefetch_related("domainalias_set"))
    if domfilter:
        domains = domains.filter(type=domfilter)
    if searchquery is not None:
        q = Q(name__contains=searchquery)
        q |= Q(domainalias__name__contains=searchquery)
        domains = domains.filter(q).distinct()
    qset_filters = events.raiseDictEvent(
        "ExtraDomainQsetFilters", domfilter, extrafilters
    )
    if qset_filters:
        domains = domains.filter(**qset_filters)
    return domains


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


def import_domain(user, row, formopts):
    """Specific code for domains import"""
    if not user.has_perm("admin.add_domain"):
        raise PermDeniedException(_("You are not allowed to import domains"))
    core_signals.can_create_object.send(
        sender="import", context=user, object_type="domains")
    dom = Domain()
    dom.from_csv(user, row)


def import_domainalias(user, row, formopts):
    """Specific code for domain aliases import"""
    if not user.has_perm("admin.add_domainalias"):
        raise PermDeniedException(
            _("You are not allowed to import domain aliases."))
    core_signals.can_create_object.send(
        sender="import", context=user, object_type="domain_aliases")
    domalias = DomainAlias()
    domalias.from_csv(user, row)


def import_account(user, row, formopts):
    """Specific code for accounts import"""
    account = User()
    account.from_csv(user, row, formopts["crypt_password"])


def _import_alias(user, row, **kwargs):
    """Specific code for aliases import"""
    alias = Alias()
    alias.from_csv(user, row, **kwargs)


def import_alias(user, row, formopts):
    _import_alias(user, row, expected_elements=4)


def import_forward(user, row, formopts):
    _import_alias(user, row, expected_elements=4)


def import_dlist(user, row, formopts):
    _import_alias(user, row)
