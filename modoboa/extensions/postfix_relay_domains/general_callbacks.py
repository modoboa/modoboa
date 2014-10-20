from django.core.urlresolvers import reverse
from django.template import Template, Context
from django.conf import settings
from django.utils.translation import ugettext_lazy
from django.db.models import Q
from modoboa.lib import events
from .models import RelayDomain, RelayDomainAlias


@events.observe('GetStaticContent')
def static_content(caller, st_type, user):
    if caller != 'domains' or st_type != 'js':
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
    return [{
        "name": "newrelaydomain",
        "label": ugettext_lazy("Add relay domain"),
        "img": "fa fa-plus",
        "modal": True,
        "modalcb": "rdomain.domainform_cb",
        "url": reverse("postfix_relay_domains:relaydomain_add")
    }]


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
            "postfix_relay_domains:relaydomain_change",
            args=[domain.id]
        ),
        'modalcb': 'rdomain.editdomain_form_cb'
    }


@events.observe('GetDomainActions')
def rdomain_actions(user, domain):
    if not isinstance(domain, RelayDomain):
        return []
    if not user.has_perm("postfix_relay_domains.delete_relaydomain"):
        return []
    return [{
        "name": "delrelaydomain",
        "url": reverse(
            "postfix_relay_domains:relaydomain_delete",
            args=[domain.id]
        ),
        "title": ugettext_lazy("Delete %s?" % domain.name),
        "img": "fa fa-trash"
    }]


@events.observe('CheckDomainName')
def check_domain_name():
    return [
        (RelayDomain, ugettext_lazy('relay domain')),
        (RelayDomainAlias, ugettext_lazy('relay domain alias'))
    ]


@events.observe('GetExtraLimitTemplates')
def extra_limit_templates():
    return [
        ('relay_domains_limit', ugettext_lazy('Relay domains'),
         ugettext_lazy('Maximum number of relay domains this user can create'),
         'Resellers'),
        ("relay_domain_aliases_limit", ugettext_lazy("Relay domain aliases"),
         ugettext_lazy('Maximum number of relay domain aliases this user can create'),
         'Resellers'),
    ]


@events.observe('ExtraDomainImportHelp')
def extra_domain_import_help():
    return [ugettext_lazy("""
<li><em>relaydomain; name; target host; service; enabled; verify recipients</em></li>
<li><em>relaydomainalias; name; target; enabled</em></li>
""")]


@events.observe('ImportObject')
def get_import_func(objtype):
    from .lib import import_relaydomain, import_relaydomainalias

    if objtype == 'relaydomain':
        return [import_relaydomain]
    if objtype == 'relaydomainalias':
        return [import_relaydomainalias]
    return []


@events.observe('ExtEnabled')
def extension_enabled(extension):
    """ExtEnabled event listener.

    Usefull when *limits* or *amavis* extensions are activated after
    *postfix_relay_domains*.

    :param extension: enabled extension
    """
    from modoboa.extensions.postfix_relay_domains import (
        init_limits_dependant_features, init_amavis_dependant_features
    )
    if extension.name == 'limits':
        init_limits_dependant_features()
    if extension.name == 'amavis':
        init_amavis_dependant_features()
