from django.utils.translation import ugettext_lazy
from modoboa.lib import events
from modoboa.lib.permissions import get_object_owner
from modoboa.extensions.limits.lib import inc_limit_usage, dec_limit_usage
from .models import RelayDomainAlias


@events.observe('GetExtraParameters')
def extra_parameters(app, level):
    from django import forms

    if app != 'limits' or level != 'A':
        return {}
    return {
        'deflt_relay_domains_limit': forms.IntegerField(
            label=ugettext_lazy("Relay domains"),
            initial=0,
            help_text=ugettext_lazy(
                "Maximum number of allowed relay domains for a new administrator"
            ),
            widget=forms.widgets.TextInput(attrs={"class": "col-md-1 form-control"})
        ),
        'deflt_relay_domain_aliases_limit': forms.IntegerField(
            label=ugettext_lazy("Relay domain aliases"),
            initial=0,
            help_text=ugettext_lazy(
                "Maximum number of allowed relay domain aliases for a new administrator"
            ),
            widget=forms.widgets.TextInput(attrs={"class": "col-md-1 form-control"})
        )
    }


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
