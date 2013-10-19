# coding: utf-8
from django.core.urlresolvers import reverse
from django.template import Template, Context
from django.conf import settings
from django.utils.translation import ugettext_lazy
from django.db.models import Q
from modoboa.lib import events, parameters
from modoboa.core.extensions import ModoExtension, exts_pool
from .models import RelayDomain, RelayDomainAlias, Service

extension_events = [
    "RelayDomainCreated",
]


class PostfixRelayDomains(ModoExtension):
    name = "postfix_relay_domains"
    label = "Postfix relay domains"
    version = "1.0"
    description = ugettext_lazy("Relay domains support for Postfix")

    def init(self):
        """Initialisation method.

        Only run once, when the extension is enabled. Populates the
        service table with default entries.
        """
        for service_name in ['relay', 'smtp']:
            Service.objects.get_or_create(name=service_name)

    def load(self):
        from .app_settings import AdminParametersForm

        parameters.register(AdminParametersForm, ugettext_lazy("Relay domains"))
        events.declare(extension_events)

    def destroy(self):
        events.unregister('GetExtraDomainEntries', extra_domain_entries)

exts_pool.register_extension(PostfixRelayDomains)


@events.observe('GetStaticContent')
def static_content(caller, user):
    if caller != 'domains':
        return []

    t = Template("""<script src="{{ STATIC_URL }}postfix_relay_domains/js/relay_domains.js" type="text/javascript"></script>
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


@events.observe('ExtraDomainMenuEntries')
def extra_domain_menu_entries(user):
    return [
        {"name": "newrelaydomain",
         "label": ugettext_lazy("Add relay domain"),
         "img": "icon-plus",
         "modal": True,
         "modalcb": "rdomain.domainform_cb",
         "url": reverse(
             "modoboa.extensions.postfix_relay_domains.views.create"
         )},
    ]


@events.observe('ExtraDomainEntries')
def extra_domain_entries(user, domfilter, searchquery, **extrafilters):
    if domfilter is not None and domfilter and domfilter != 'relaydomain':
        return []
    relay_domains = RelayDomain.objects.get_for_admin(user)
    if searchquery is not None:
        q = Q(name__contains=searchquery)
        q |= Q(relaydomainalias__name__contains=searchquery)
        relay_domains = relay_domains.filter(q).distinct()
    if 'srvfilter' in extrafilters and extrafilters['srvfilter']:
        relay_domains = relay_domains.filter(
            Q(service__name=extrafilters['srvfilter'])
        )
    return relay_domains


@events.observe('GetDomainModifyLink')
def rdomain_modify_link(domain):
    if not isinstance(domain, RelayDomain):
        return {}
    return {
        'url': reverse(
            'modoboa.extensions.postfix_relay_domains.views.edit',
            args=[domain.id]
        ),
        'modalcb': 'rdomain.domainform_cb'
    }


@events.observe('GetDomainAliasQuerySet')
def get_da_query_set(domain):
    if domain.__class__.__name__ != 'RelayDomain':
        return []
    return [domain.relaydomainalias_set]


@events.observe('GetDomainActions')
def rdomain_actions(user, domain):
    if not isinstance(domain, RelayDomain):
        return []
    if not user.has_perm("postfix_relay_domains.delete_relaydomain"):
        return []
    return [{
        "name": "delrelaydomain",
        "url": reverse("modoboa.extensions.postfix_relay_domains.views.delete",
                       args=[domain.id]),
        "title": ugettext_lazy("Delete %s?" % domain.name),
        "img": "icon-trash"
    }]


@events.observe('CheckDomainName')
def check_domain_name():
    return [
        (RelayDomain, ugettext_lazy('relay domain')),
        (RelayDomainAlias, ugettext_lazy('relay domain alias'))
    ]
