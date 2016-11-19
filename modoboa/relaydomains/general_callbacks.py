"""General event callbacks."""

from django.utils.translation import ugettext_lazy, ugettext as _

from modoboa.lib import events

from .forms import RelayDomainWizardStep, RelayDomainFormGeneral


@events.observe('ExtraDomainFilters')
def extra_domain_filters():
    return ['srvfilter']


@events.observe("ExtraDomainTypes")
def extra_domain_types():
    """Declare the relay domain type."""
    return [("relaydomain", _("Relay domain"))]


@events.observe("ExtraDomainWizardSteps")
def extra_wizard_step():
    """Return a step to configure the relay settings."""
    return [RelayDomainWizardStep(
        "relay", RelayDomainFormGeneral, _("Relay domain"),
        "relaydomains/relaydomain_form.html"
    )]


@events.observe("ExtraDomainForm")
def extra_domain_form(user, domain):
    """Return relay settings for domain edition."""
    if not user.has_perm("relaydomains.change_relaydomain"):
        return []
    if domain.type != "relaydomain":
        return []
    return [{
        "id": "relaydomain", "title": _("Relay settings"),
        "cls": RelayDomainFormGeneral,
        "formtpl": "relaydomains/relaydomain_form.html"
    }]


@events.observe("FillDomainInstances")
def fill_domain_instances(user, domain, instances):
    """Fill the relaydomain form with the right instance."""
    if not user.has_perm("relaydomains.change_relaydomain"):
        return
    if domain.type != "relaydomain":
        return
    instances["relaydomain"] = domain.relaydomain


@events.observe("ExtraDomainQsetFilters")
def extra_domain_entries(domfilter, extrafilters):
    """Return extra queryset filters."""
    if domfilter is not None and domfilter and domfilter != 'relaydomain':
        return {}
    if "srvfilter" in extrafilters and extrafilters["srvfilter"]:
        return {"relaydomain__service__name": extrafilters["srvfilter"]}
    return {}


@events.observe("GetTagsForDomain")
def get_tags_for_domain(domain):
    """Return relay domain custom tags."""
    if domain.type != "relaydomain":
        return []
    return domain.relaydomain.tags


@events.observe('ExtraDomainImportHelp')
def extra_domain_import_help():
    return [ugettext_lazy("""
<li><em>relaydomain; name; target host; service; enabled; verify recipients</em></li>
""")]


@events.observe('ImportObject')
def get_import_func(objtype):
    from .lib import import_relaydomain

    if objtype == 'relaydomain':
        return [import_relaydomain]
    return []
