"""General event callbacks."""

from django.conf import settings
from django.template import Template, Context
from django.utils.translation import ugettext_lazy, ugettext as _

from modoboa.lib import events

from .forms import RelayDomainWizardStep, RelayDomainFormGeneral

PERMISSIONS = {
    "Resellers": [
        ("relaydomains", "relaydomain", "add_relaydomain"),
        ("relaydomains", "relaydomain", "change_relaydomain"),
        ("relaydomains", "relaydomain", "delete_relaydomain"),
        ("relaydomains", "service", "add_service"),
        ("relaydomains", "service", "change_service"),
        ("relaydomains", "service", "delete_service")
    ]
}


@events.observe("GetExtraRolePermissions")
def extra_permissions(rolename):
    """Return extra permissions for Resellers."""
    return PERMISSIONS.get(rolename, [])


@events.observe('GetStaticContent')
def static_content(caller, st_type, user):
    if caller != 'domains' or st_type != 'js':
        return []

    t = Template("""<script src="{{ STATIC_URL }}relaydomains/js/relay_domains.js" type="text/javascript"></script>
<script type="text/javascript">
  var rdomain;
  $(document).ready(function() {
    rdomain = new RelayDomains({});
  });
</script>
""")
    return [t.render(Context({'STATIC_URL': settings.STATIC_URL}))]


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
