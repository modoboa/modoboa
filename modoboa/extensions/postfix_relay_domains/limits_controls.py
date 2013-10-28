from modoboa.lib import events
from modoboa.lib.permissions import get_object_owner
from modoboa.extensions.limits.lib import inc_limit_usage, dec_limit_usage
from .models import RelayDomainAlias


@events.observe('RelayDomainCreated')
def inc_relaydomains_count(user, rdomain):
    inc_limit_usage(user, 'relay_domains_limit')


@events.observe('RelayDomainDeleted')
def dec_relaydomains_count(rdomain):
    owner = get_object_owner(rdomain)
    dec_limit_usage(owner, 'relay_domains_limit')
    for rdomalias in rdomain.relaydomainalias_set.all():
        dec_rdomaliases_count(rdomalias)


@events.observe('RelayDomainAliasCreated')
def inc_rdomaliases_count(user, rdomalias):
    inc_limit_usage(user, 'relay_domain_aliases_limit')


@events.observe('RelayDomainAliasDeleted')
def dec_rdomaliases_count(rdomainaliases):
    if isinstance(rdomainaliases, RelayDomainAlias):
        rdomainaliases = [rdomainaliases]
    for rdomainalias in rdomainaliases:
        owner = get_object_owner(rdomainalias)
        dec_limit_usage(owner, 'relay_domain_aliases_limit')
