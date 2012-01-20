# coding: utf-8
"""
:mod:`controls` --- provides event handlers that check if limits are reached
----------------------------------------------------------------------------

"""
from modoboa.admin.models import Mailbox
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
    if not is_reseller(user):
        return
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

@events.observe('CanCreateDomain')
def check_domains_limit(user):
    check_limit(user, 'domains_limit')

@events.observe('CreateDomain')
def inc_nb_domains(user, domain):
    inc_limit(user, 'domains_limit')

@events.observe('DeleteDomain')
def dec_nb_domains(user, domain):
    dec_limit(user, 'domains_limit')

@events.observe('CanCreateDomainAlias')
def check_domaliases_limit(user):
    check_limit(user, 'domain_aliases_limit')

@events.observe('DomainAliasCreated')
def inc_nb_domaliases(user, domalias):
    inc_limit(user, 'domain_aliases_limit')

@events.observe('DomainAliasDeleted')
def dec_nb_domaliases(user, domainalias):
    dec_limit(user, 'domain_aliases_limit')

@events.observe('CanCreateMailbox')
def check_mboxes_limit(user):
    check_limit(user, 'mailboxes_limit')

@events.observe('CreateMailbox')
def inc_nb_mailboxes(user, mailbox):
    inc_limit(user, 'mailboxes_limit')

@events.observe('DeleteMailbox')
def dec_nb_mailboxes(user, mailbox):
    dec_limit(user, 'mailboxes_limit')

@events.observe('CanCreateMailboxAlias')
def check_mbaliases_limit(user):
    check_limit(user, 'mailbox_aliases_limit')

@events.observe('MailboxAliasCreated')
def inc_nb_mbaliases(user, mailboxalias):
    inc_limit(user, 'mailbox_aliases_limit')
