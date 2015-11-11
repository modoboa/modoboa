# coding: utf-8
"""
:mod:`controls` --- provides event handlers that check if limits are reached
----------------------------------------------------------------------------

"""

from modoboa.lib import events
from modoboa.lib.permissions import get_object_owner

import modoboa.admin.models as admin_models

from .lib import LimitReached, inc_limit_usage, dec_limit_usage
from .models import LimitTemplates, LimitsPool


def check_limit(user, lname, count=1):
    """Check if a user has reached a defined limit

    We check if the user will not reach the given limit after this
    creation.

    :param user: a ``User`` object
    :param int count: the number of objects the user tries to create
    :raises: ``LimitReached``
    """
    try:
        if user.limitspool.will_be_reached(lname, count):
            raise LimitReached(user.limitspool.get_limit(lname))
    except LimitsPool.DoesNotExist:
        pass


def move_pool_resource(owner, user):
    """Move resource from one pool to another

    When an account doesn't need a pool anymore, we move the
    associated resource to the pool of its owner.
    """
    if not hasattr(user, "limitspool"):
        return
    if not owner.is_superuser:
        for ltpl in LimitTemplates().templates:
            l = user.limitspool.get_limit(ltpl[0])
            if l.maxvalue < 0:
                continue
            ol = owner.limitspool.get_limit(ltpl[0])
            ol.curvalue += l.curvalue
            ol.maxvalue += l.maxvalue
            ol.save()

    user.limitspool.delete()


@events.observe('DomainCreated')
def inc_nb_domains(user, domain):
    inc_limit_usage(user, 'domains_limit')


@events.observe('DomainDeleted')
def dec_nb_domains(domain, owner=None):
    if owner is None:
        owner = get_object_owner(domain)
    dec_limit_usage(owner, 'domains_limit')
    for domalias in domain.domainalias_set.all():
        dec_nb_domaliases(domalias)
    for mailbox in domain.mailbox_set.all():
        dec_nb_mailboxes(mailbox)
    for mbalias in domain.alias_set.all():
        dec_nb_mbaliases(mbalias)


@events.observe('DomainAliasCreated')
def inc_nb_domaliases(user, domalias):
    inc_limit_usage(user, 'domain_aliases_limit')


@events.observe('DomainAliasDeleted')
def dec_nb_domaliases(domainaliases):
    if isinstance(domainaliases, admin_models.DomainAlias):
        domainaliases = [domainaliases]
    for domainalias in domainaliases:
        owner = get_object_owner(domainalias)
        dec_limit_usage(owner, 'domain_aliases_limit')


@events.observe('MailboxCreated')
def inc_nb_mailboxes(user, mailbox):
    inc_limit_usage(user, 'mailboxes_limit')


@events.observe('MailboxDeleted')
def dec_nb_mailboxes(mailboxes):
    if isinstance(mailboxes, admin_models.Mailbox):
        mailboxes = [mailboxes]
    for mailbox in mailboxes:
        owner = get_object_owner(mailbox)
        dec_limit_usage(owner, 'mailboxes_limit')


@events.observe('MailboxAliasCreated')
def inc_nb_mbaliases(user, mailboxalias):
    inc_limit_usage(user, 'mailbox_aliases_limit')


@events.observe('MailboxAliasDeleted')
def dec_nb_mbaliases(mailboxaliases):
    if isinstance(mailboxaliases, admin_models.Alias):
        mailboxaliases = [mailboxaliases]
    for alias in mailboxaliases:
        owner = get_object_owner(alias)
        dec_limit_usage(owner, 'mailbox_aliases_limit')


@events.observe('CanCreate')
def can_create_new_object(user, objtype, count=1):
    check_limit(user, '%s_limit' % objtype, count)


@events.observe("AccountCreated")
def create_pool(user):
    owner = get_object_owner(user)
    if owner.group not in ['SuperAdmins', 'Resellers']:
        return

    if user.group == 'DomainAdmins':
        check_limit(owner, 'domain_admins_limit')
        inc_limit_usage(owner, 'domain_admins_limit')

    if user.group in ['DomainAdmins', 'Resellers']:
        p, created = LimitsPool.objects.get_or_create(user=user)
        p.create_limits(owner)


@events.observe("UserCanSetRole")
def user_can_set_role(user, role, account=None):
    """Check if the user can still set this role.

    The only interesting case concerns resellers defining new domain
    administrators. We want to check if they are allowed to do this
    operation before any modification is made to :keyword:`account`.

    :param ``User`` user: connected user
    :param ``User`` account: account modified (None on creation)
    :param str newrole: role to check
    """
    if role == 'DomainAdmins':
        lname = 'domain_admins_limit'
    else:
        return [True]
    if user.is_superuser or not user.limitspool.will_be_reached(lname):
        return [True]
    if account is not None and account.group == role:
        return [True]
    return [False]


@events.observe("AccountModified")
def on_account_modified(old, new):
    """Update limits when roles are updated"""
    owner = get_object_owner(old)
    if owner.group not in ["SuperAdmins", "Resellers"]:
        # Domain admins can't change the role so nothing to check.
        return

    if new.group != "SuperAdmins":
        # Check if account needs a pool (case: a superadmin is
        # downgraded)
        if not hasattr(new, "limitspool"):
            p = LimitsPool(user=new)
            p.save()
            p.create_limits(owner)

    if new.group not in ["DomainAdmins", "Resellers"]:
        move_pool_resource(owner, new)

    if old.oldgroup == "DomainAdmins":
        if new.group != "DomainAdmins":
            dec_limit_usage(owner, 'domain_admins_limit')
        return

    if new.group == "DomainAdmins":
        check_limit(owner, 'domain_admins_limit')
        inc_limit_usage(owner, 'domain_admins_limit')


@events.observe("AccountDeleted")
def on_account_deleted(account, byuser, **kwargs):
    owner = get_object_owner(account)
    if owner.group not in ["SuperAdmins", "Resellers"]:
        return

    move_pool_resource(owner, account)

    if account.group == "DomainAdmins":
        dec_limit_usage(owner, 'domain_admins_limit')


@events.observe('DomainOwnershipRemoved')
def domain_ownership_removed(reseller, domain):
    """DomainOwnershipRemoved listener.

    The access :keyword:`reseller` had to :keyword:`domain` has been
    removed by a super adminstrator. We must decrement all limit
    usages.

    :param ``User`` reseller: reseller that created :keyword:`domain`
    :param ``Domain`` domain: domain
    """
    dec_nb_domains(domain, reseller)
    for dadmin in domain.admins:
        if reseller.is_owner(dadmin):
            dec_limit_usage(reseller, 'domain_admins_limit')
