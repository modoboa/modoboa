# -*- coding: utf-8 -*-

"""Internal library for admin."""

from __future__ import unicode_literals

import ipaddress
import logging
import random
import string
from functools import wraps
from itertools import chain

import dns.resolver
from dns.name import IDNA_2008_UTS_46

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.encoding import smart_text
from django.utils.translation import ugettext as _

from modoboa.core import signals as core_signals
from modoboa.core.models import User
from modoboa.lib.exceptions import PermDeniedException
from modoboa.parameters import tools as param_tools
from . import signals
from .models import Alias, Domain, DomainAlias


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
            .values_list("object_id", flat=True)
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
            .values_list("object_id", flat=True)
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
    results = signals.extra_domain_qset_filters.send(
        sender="get_domains", domfilter=domfilter, extrafilters=extrafilters)
    if results:
        qset_filters = {}
        for result in results:
            qset_filters.update(result[1])
        domains = domains.filter(**qset_filters)
    return domains


def check_if_domain_exists(name, dtypes):
    """Check if a domain already exists.

    We not only look for domains, we also look for every object that
    could conflict with a domain (domain alias, etc.)

    """
    for dtype, label in dtypes:
        if dtype.objects.filter(name=name).exists():
            return label
    return None


def import_domain(user, row, formopts):
    """Specific code for domains import"""
    if not user.has_perm("admin.add_domain"):
        raise PermDeniedException(_("You are not allowed to import domains"))
    core_signals.can_create_object.send(
        sender="import", context=user, klass=Domain)
    dom = Domain()
    dom.from_csv(user, row)


def import_domainalias(user, row, formopts):
    """Specific code for domain aliases import"""
    if not user.has_perm("admin.add_domainalias"):
        raise PermDeniedException(
            _("You are not allowed to import domain aliases."))
    core_signals.can_create_object.send(
        sender="import", context=user, klass=DomainAlias)
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


def get_domain_mx_list(domain):
    """Return a list of MX IP address for domain."""
    result = []
    logger = logging.getLogger("modoboa.admin")
    dns_server = param_tools.get_global_parameter("custom_dns_server")
    if dns_server:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [dns_server]
    else:
        resolver = dns.resolver

    try:
        dns_answers = resolver.query(domain, "MX")
    except dns.resolver.NXDOMAIN as e:
        logger.error(_("No DNS records found for %s") % domain, exc_info=e)
    except dns.resolver.NoAnswer as e:
        logger.error(_("No MX record for %s") % domain, exc_info=e)
    except dns.resolver.NoNameservers as e:
        logger.error(_("No working name servers found"), exc_info=e)
    except dns.resolver.Timeout as e:
        logger.warning(
            _("DNS resolution timeout, unable to query %s at the moment") %
            domain, exc_info=e)
    else:
        for dns_answer in dns_answers:
            for rtype in ["A", "AAAA"]:
                try:
                    mx_domain = dns_answer.exchange.to_unicode(
                        omit_final_dot=True, idna_codec=IDNA_2008_UTS_46)
                    ip_answers = resolver.query(mx_domain, rtype)
                except dns.resolver.NXDOMAIN as e:
                    logger.error(
                        _("No {type} record found for MX {mx}").format(
                            type=rtype, mx=domain), exc_info=e)
                except dns.resolver.NoAnswer:
                    pass
                else:
                    for ip_answer in ip_answers:
                        try:
                            address_smart = smart_text(ip_answer.address)
                            mx_ip = ipaddress.ip_address(address_smart)
                        except ValueError as e:
                            logger.warning(
                                _("Invalid IP address format for "
                                  "{domain}; {addr}").format(
                                      domain=mx_domain,
                                      addr=smart_text(ip_answer.address)
                                  ), exc_info=e)
                        else:
                            result.append((mx_domain, mx_ip))
    return result


def domain_has_authorized_mx(name):
    """Check if domain has authorized mx record at least."""
    valid_mxs = param_tools.get_global_parameter("valid_mxs")
    valid_mxs = [ipaddress.ip_network(smart_text(v.strip()))
                 for v in valid_mxs.split() if v.strip()]
    domain_mxs = get_domain_mx_list(name)
    for _mx_addr, mx_ip_addr in domain_mxs:
        for subnet in valid_mxs:
            if mx_ip_addr in subnet:
                return True
    return False


def make_password():
    """Create a random password."""
    length = int(
        param_tools.get_global_parameter("random_password_length", app="core")
    )
    return "".join(
        random.SystemRandom().choice(
            string.ascii_letters + string.digits) for _ in range(length))
