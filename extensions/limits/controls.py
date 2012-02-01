# coding: utf-8
"""
:mod:`controls` --- provides event handlers that check if limits are reached
----------------------------------------------------------------------------

"""
from modoboa.admin.models import Mailbox
from modoboa.admin.lib import \
    get_object_owner, grant_access_to_object, \
    ungrant_access_to_object
from modoboa.lib import events
from lib import *
from models import *

def check_limit(user, lname):
    """Check if a user has reached a defined limit

    We check if the user will not reach the given limit after this
    creation. 

    Raise a ``LimitReached`` exception if the limit is reached.

    :param user: a ``User`` object
    """
    try:
        if user.limitspool.will_be_reached(lname):
            raise LimitReached(user.limitspool.get_limit(lname))
    except LimitsPool.DoesNotExist:
        pass

def inc_limit(user, lname):
    try:
        user.limitspool.inc_curvalue(lname)
    except LimitsPool.DoesNotExist:
        pass

def dec_limit(user, lname):
    try:
        user.limitspool.dec_curvalue(lname)
    except LimitsPool.DoesNotExist:
        pass


@events.observe('CreateDomain')
def inc_nb_domains(user, domain):
    inc_limit(user, 'domains_limit')

@events.observe('DeleteDomain')
def dec_nb_domains(domain):
    owner = get_object_owner(domain)
    dec_limit(owner, 'domains_limit')
    for domalias in domain.domainalias_set.all():
        dec_nb_domaliases(domalias)
    for mailbox in domain.mailbox_set.all():
        dec_nb_mailboxes(mailbox)
    for mbalias in domain.alias_set.all():
        dec_nb_mbaliases(mbalias)

@events.observe('DomainAliasCreated')
def inc_nb_domaliases(user, domalias):
    inc_limit(user, 'domain_aliases_limit')

@events.observe('DomainAliasDeleted')
def dec_nb_domaliases(domainalias):
    owner = get_object_owner(domainalias)
    dec_limit(owner, 'domain_aliases_limit')

@events.observe('CreateMailbox')
def inc_nb_mailboxes(user, mailbox):
    inc_limit(user, 'mailboxes_limit')

@events.observe('DeleteMailbox')
def dec_nb_mailboxes(mailbox):
    owner = get_object_owner(mailbox)
    dec_limit(owner, 'mailboxes_limit')

@events.observe('MailboxAliasCreated')
def inc_nb_mbaliases(user, mailboxalias):
    inc_limit(user, 'mailbox_aliases_limit')

@events.observe('MailboxAliasDeleted')
def dec_nb_mbaliases(mailboxalias):
    owner = get_object_owner(mailboxalias)
    dec_limit(owner, 'mailbox_aliases_limit')

@events.observe('CanCreate')
def can_create_new_object(user, objtype):
    check_limit(user, '%s_limit' % objtype)

@events.observe("DomainAdminCreated")
def create_pool(user):
    owner = get_object_owner(user)
    inc_limit(owner, 'domain_admins_limit')
    p = LimitsPool(user=user)
    p.save()
    p.create_limits()

@events.observe("DomainAdminDeleted")
def create_pool(da):
    owner = get_object_owner(da)
    dec_limit(owner, 'domain_admins_limit')

@events.observe("DomainAdminDeleted", "SuperAdminPromotion")
def move_pool_resource(user):
    owner = get_object_owner(user)
    if not owner.is_superuser:
        for ooentry in user.objectaccess_set.all():
            if ooentry.is_owner:
                grant_access_to_object(owner, ooentry.content_object, True)
            ooentry.delete()

        for lname in reseller_limits_tpl:
            l = user.limitspool.get_limit(lname)
            ol = owner.limitspool.get_limit(lname)
            ol.curvalue += l.curvalue
            ol.maxvalue += l.maxvalue
            ol.save()

    user.limitspool.delete()
