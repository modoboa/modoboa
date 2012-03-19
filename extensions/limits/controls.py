# coding: utf-8
"""
:mod:`controls` --- provides event handlers that check if limits are reached
----------------------------------------------------------------------------

"""
from modoboa.lib import events
from lib import *
from models import *
from modoboa.lib.permissions import get_object_owner

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

def move_pool_resource(owner, user):
    try:
        pool = user.limitspool
    except LimitsPool.DoesNotExist:
        return
    if not owner.is_superuser:
        for lname in reseller_limits_tpl:
            l = user.limitspool.get_limit(lname)
            if l.maxvalue < 0:
                continue
            ol = owner.limitspool.get_limit(lname)
            ol.curvalue += l.curvalue
            ol.maxvalue += l.maxvalue
            ol.save()

    user.limitspool.delete()

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
def dec_nb_domaliases(domainaliases):
    from modoboa.admin.models import DomainAlias

    if isinstance(domainaliases, DomainAlias):
        domainaliases = [domainaliases]
    for domainalias in domainaliases:
        owner = get_object_owner(domainalias)
        dec_limit(owner, 'domain_aliases_limit')

@events.observe('CreateMailbox')
def inc_nb_mailboxes(user, mailbox):
    inc_limit(user, 'mailboxes_limit')

@events.observe('DeleteMailbox')
def dec_nb_mailboxes(mailboxes):
    from modoboa.admin.models import Mailbox

    if isinstance(mailboxes, Mailbox):
        mailboxes = [mailboxes]
    for mailbox in mailboxes:
        owner = get_object_owner(mailbox)
        dec_limit(owner, 'mailboxes_limit')
        # FIXME: Gestion des alias ici

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

@events.observe("AccountCreated")
def create_pool(user):
    owner = get_object_owner(user)
    if not owner.is_superuser and \
       not owner.belongs_to_group("Resellers"):
        return

    if user.belongs_to_group("DomainAdmins"):
        check_limit(owner, 'domain_admins_limit')
        inc_limit(owner, 'domain_admins_limit')

    if user.belongs_to_group("DomainAdmins") or \
       user.belongs_to_group("Resellers"):
        p = LimitsPool(user=user)
        p.save()
        p.create_limits()

@events.observe("AccountModified")
def on_account_modified(old, new):
    owner = get_object_owner(old)
    if owner.group not in ["SuperAdmins", "Resellers"]:
        return

    if not new.group in ["DomainAdmins", "Resellers"]:
        move_pool_resource(owner, new)

    if old.oldgroup == "DomainAdmins":
        if new.group != "DomainAdmins":
            dec_limit(owner, 'domain_admins_limit')
        return
    
    if new.group == "DomainAdmins":
        check_limit(owner, 'domain_admins_limit')
        inc_limit(owner, 'domain_admins_limit')

@events.observe("AccountDeleted")
def on_account_deleted(account):
    owner = get_object_owner(account)
    if not owner.group in ["SuperAdmins", "Resellers"]:
        return

    move_pool_resource(owner, account)

    if account.group == "DomainAdmins":
        dec_limit(owner, 'domain_admins_limit')
