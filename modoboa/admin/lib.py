"""Internal library for admin."""

import csv
import io
import ipaddress
import logging
import random
import string
from functools import wraps
from itertools import chain

import dns.resolver
from dns.name import IDNA_2008_UTS_46

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from django.contrib.auth import password_validation
from django.contrib.contenttypes.models import ContentType

from reversion import revisions as reversion

from modoboa.core import signals as core_signals
from modoboa.core.models import User
from modoboa.lib.exceptions import Conflict, ModoboaException, PermDeniedException
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
        ids = user.objectaccess_set.filter(
            content_type=ContentType.objects.get_for_model(user)
        ).values_list("object_id", flat=True)
        q = Q(pk__in=ids)
        if searchquery is not None:
            q &= Q(username__icontains=searchquery) | Q(email__icontains=searchquery)
        if grpfilter is not None and grpfilter:
            if grpfilter == "SuperAdmins":
                q &= Q(is_superuser=True)
            else:
                q &= Q(groups__name=grpfilter)
        accounts = User.objects.filter(q).prefetch_related("groups")

    aliases = []
    if (
        idtfilter is None
        or not idtfilter
        or (idtfilter in ["alias", "forward", "dlist"])
    ):
        alct = ContentType.objects.get_for_model(Alias)
        ids = user.objectaccess_set.filter(content_type=alct).values_list(
            "object_id", flat=True
        )
        q = Q(pk__in=ids, internal=False)
        if searchquery is not None:
            q &= Q(address__icontains=searchquery) | Q(
                domain__name__icontains=searchquery
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
    domains = Domain.objects.get_for_admin(user).prefetch_related("domainalias_set")
    if domfilter:
        domains = domains.filter(type=domfilter)
    if searchquery is not None:
        q = Q(name__contains=searchquery)
        q |= Q(domainalias__name__contains=searchquery)
        domains = domains.filter(q).distinct()
    results = signals.extra_domain_qset_filters.send(
        sender="get_domains", domfilter=domfilter, extrafilters=extrafilters
    )
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
    core_signals.can_create_object.send(sender="import", context=user, klass=Domain)
    dom = Domain()
    dom.from_csv(user, row)


def import_domainalias(user, row, formopts):
    """Specific code for domain aliases import"""
    if not user.has_perm("admin.add_domainalias"):
        raise PermDeniedException(_("You are not allowed to import domain aliases."))
    core_signals.can_create_object.send(
        sender="import", context=user, klass=DomainAlias
    )
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
    _import_alias(user, row, expected_elements=4, formopts=formopts)


def import_forward(user, row, formopts):
    _import_alias(user, row, expected_elements=4, formopts=formopts)


def import_dlist(user, row, formopts):
    _import_alias(user, row, formopts=formopts)


def get_dns_resolver():
    """Return a DNS resolver object."""
    dns_server = param_tools.get_global_parameter("custom_dns_server")
    if dns_server:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [dns_server]
    else:
        resolver = dns.resolver
    return resolver


def get_authoritative_server(domain, resolver=None):
    if not resolver:
        resolver = get_dns_resolver()

    dnsname = dns.name.from_text(domain)

    while True:
        try:
            answers = dns.resolver.resolve(dnsname, "NS")
            if answers:
                first_answer = answers[0]
                if hasattr(first_answer, "target"):
                    return str(first_answer.target)
                if hasattr(first_answer, "address"):
                    return str(first_answer.address)
        except dns.resolver.NoAnswer:
            dnsname = dnsname.parent()
        else:
            dnsname = dnsname.parent()


def get_authoritative_ip(domain, resolver=None):
    dnsserver_name = get_authoritative_server(domain, resolver=resolver)
    if not resolver:
        resolver = get_dns_resolver()
    answer = resolver.resolve(dnsserver_name)
    if answer:
        return answer[0].address
    return None


def get_authoritative_resolver(domain, resolver=None):
    dnsserver_ip = get_authoritative_ip(domain, resolver=resolver)
    if dnsserver_ip:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [dnsserver_ip]
    else:
        resolver = get_dns_resolver()
    return resolver


def get_dns_records(name, typ, resolver=None):
    """Retrieve DNS records for given name and type."""
    logger = logging.getLogger("modoboa.admin")

    try:
        resolver = get_authoritative_resolver(name, resolver=resolver)
        dns_answers = resolver.resolve(name, typ, search=True)
    except dns.resolver.NXDOMAIN as e:
        logger.error(_("No DNS record found for %s") % name, exc_info=e)
    except dns.resolver.NoAnswer as e:
        logger.error(
            _("No %(type)s record for %(name)s") % {"type": typ, "name": name},
            exc_info=e,
        )
    except dns.resolver.NoNameservers as e:
        logger.error(_("No working name servers found"), exc_info=e)
    except dns.resolver.Timeout as e:
        logger.warning(
            _("DNS resolution timeout, unable to query %s at the moment") % name,
            exc_info=e,
        )
    except dns.name.NameTooLong as e:
        logger.error(_("DNS name is too long: {}".format(name)), exc_info=e)
    else:
        return dns_answers
    return None


def get_domain_mx_list(domain):
    """Return a list of MX IP address for domain."""
    result = []
    logger = logging.getLogger("modoboa.admin")
    resolver = get_dns_resolver()
    dns_answers = get_dns_records(domain, "MX", resolver)
    if dns_answers is None:
        return result
    for dns_answer in dns_answers:
        mx_domain = dns_answer.exchange.to_unicode(
            omit_final_dot=True, idna_codec=IDNA_2008_UTS_46
        )
        rtypes = ["A"]
        if param_tools.get_global_parameter("enable_ipv6_mx_checks", app="admin"):
            rtypes.append("AAAA")
        for rtype in rtypes:
            ip_answers = get_dns_records(mx_domain, rtype, resolver)
            if not ip_answers:
                continue
            for ip_answer in ip_answers:
                try:
                    address_smart = smart_str(ip_answer.address)
                    mx_ip = ipaddress.ip_address(address_smart)
                except ValueError as e:
                    logger.warning(
                        _("Invalid IP address format for " "{domain}; {addr}").format(
                            domain=mx_domain, addr=smart_str(ip_answer.address)
                        ),
                        exc_info=e,
                    )
                else:
                    result.append((mx_domain, mx_ip))
    return result


def domain_has_authorized_mx(name):
    """Check if domain has authorized mx record at least."""
    valid_mxs = param_tools.get_global_parameter("valid_mxs")
    valid_mxs = [
        ipaddress.ip_network(smart_str(v.strip()))
        for v in valid_mxs.split()
        if v.strip()
    ]
    domain_mxs = get_domain_mx_list(name)
    for _mx_addr, mx_ip_addr in domain_mxs:
        for subnet in valid_mxs:
            if mx_ip_addr in subnet:
                return True
    return False


def make_password():
    """Create a random password."""
    length = int(param_tools.get_global_parameter("random_password_length", app="core"))
    allow_special_characters = bool(param_tools.get_global_parameter("allow_special_characters", app="core"))
    possible_chars = string.ascii_letters + string.digits
    for i in range(10): # limit tries
        if allow_special_characters: # add special characters in random passwd
            possible_chars += string.punctuation
        password = "".join(
            random.SystemRandom().choice(possible_chars) for _ in range(length)
        )
        try:
            password_validation.validate_password(password)
        except ValidationError:
            continue
        return password


@reversion.create_revision()
def import_data(user, file_object, options: dict):
    """Generic import function

    As the process of importing data from a CSV file is the same
    whatever the type, we do a maximum of the work here.
    """
    try:
        infile = io.TextIOWrapper(file_object.file, encoding="utf8")
        reader = csv.reader(infile, delimiter=options["sepchar"])
    except csv.Error as inst:
        error = str(inst)
    else:
        try:
            cpt = 0
            for row in reader:
                if not row:
                    continue
                fct = signals.import_object.send(
                    sender="importdata", objtype=row[0].strip()
                )
                fct = [func for x_, func in fct if func is not None]
                if not fct:
                    continue
                fct = fct[0]
                with transaction.atomic():
                    try:
                        fct(user, row, options)
                    except Conflict:
                        if options["continue_if_exists"]:
                            continue
                        raise Conflict(
                            _("Object already exists: %s")
                            % options["sepchar"].join(row[:2])
                        ) from None
                cpt += 1
            msg = _("%d objects imported successfully") % cpt
            return True, msg
        except ModoboaException as e:
            error = str(e)
    return False, error
