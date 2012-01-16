# coding: utf-8
"""
:mod:`controls` --- provides event handlers to check if limits are reached
--------------------------------------------------------------------------

"""

from lib import *
from models import *

def check_domains_limit(user):
    """Check if user has reached its limit for domains creation

    Raise a ``LimitReached`` exception if the limit is reached.

    :param user: a ``User`` object
    """
    if not is_reseller(user):
        return
    if not user.limitspool.inc_curvalue('domains_limit'):
        raise LimitReached(user.limitspool.get_limit('domains_limit'))

def associate_domain_to_reseller(user, domain):
    if not is_reseller(user):
        return
    ro = ResellerObject(user=user, content_object=domain)
    ro.save()

def get_reseller_domains(user):
    qs = user.resellerobject_set.filter(content_type__app_label="admin",
                                        content_type__model="domain")
    domains = []
    for ro in qs.all():
        domains += [ro.content_object]
    return domains

def check_domaliases_limit(user, domalias):
    pass

def check_mboxes_limit(user, mbox):
    pass

def check_mbaliases_limit(user, mbalias):
    pass
