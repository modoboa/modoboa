"""Django signal handlers for relaydomains."""

from django.conf import settings
from django.db.models import signals
from django.dispatch import receiver
from django.template import Template, Context
from django.utils.translation import ugettext as _

from modoboa.admin import models as admin_models
from modoboa.admin import signals as admin_signals
from modoboa.core import signals as core_signals
from modoboa.lib.email_utils import split_mailbox

from . import constants
from . import forms
from . import lib
from . import models
from . import postfix_maps


@receiver(admin_signals.use_external_recipients)
def check_relaydomain_alias(sender, **kwargs):
    """Allow the creation of an alias on a relaydomain."""
    recipient = kwargs.get("recipients")
    if not recipient:
        return
    localpart, domain = split_mailbox(recipient)
    if not (models.RelayDomain.objects.select_related().filter(
            domain__name=domain).exists()):
        return False
    if (admin_models.Mailbox.objects.select_related("domain").filter(
            domain__name=domain, address=localpart).exists()):
        return False
    return True


@receiver(signals.post_save, sender=admin_models.Domain)
def clean_domain(sender, instance, **kwargs):
    """Remove or create RelayDomain record if needed."""
    if kwargs.get("created"):
        return
    if instance.type == "domain":
        try:
            instance.relaydomain.delete()
        except models.RelayDomain.DoesNotExist:
            pass
    else:
        # Make sure to create a RelayDomain instance since we can't do it
        # at form level...
        models.RelayDomain.objects.get_or_create(
            domain=instance,
            defaults={"service": models.Service.objects.first()}
        )


@receiver(core_signals.register_postfix_maps)
def register_postfix_maps(sender, **kwargs):
    """Register postfix maps."""
    return [
        postfix_maps.RelayDomainsMap,
        postfix_maps.RelayDomainsTransportMap,
        postfix_maps.SplitedDomainsTransportMap,
        postfix_maps.RelayRecipientVerification
    ]


@receiver(core_signals.extra_role_permissions)
def extra_role_permissions(sender, role, **kwargs):
    """Add permissions to the Resellers group."""
    return constants.PERMISSIONS.get(role, [])


@receiver(core_signals.extra_static_content)
def static_content(sender, caller, st_type, user, **kwargs):
    """Add extra static content."""
    if caller != "domains" or st_type != "js":
        return ""

    t = Template("""<script src="{{ STATIC_URL }}relaydomains/js/relay_domains.js" type="text/javascript"></script>
<script type="text/javascript">
  var rdomain;
  $(document).ready(function() {
    rdomain = new RelayDomains({});
  });
</script>
""")
    return t.render(Context({"STATIC_URL": settings.STATIC_URL}))


@receiver(admin_signals.extra_domain_filters)
def extra_domain_filters(sender, **kwargs):
    """Return relaydomain filters."""
    return ["srvfilter"]


@receiver(admin_signals.extra_domain_forms)
def extra_domain_form(sender, user, **kwargs):
    """Return relay settings for domain edition."""
    if not user.has_perm("relaydomains.change_relaydomain"):
        return []
    domain = kwargs.get("domain")
    if not domain or domain.type != "relaydomain":
        return []
    return [{
        "id": "relaydomain", "title": _("Relay settings"),
        "cls": forms.RelayDomainFormGeneral,
        "formtpl": "relaydomains/relaydomain_form.html"
    }]


@receiver(admin_signals.get_domain_form_instances)
def fill_domain_instances(sender, user, domain, **kwargs):
    """Fill the relaydomain form with the right instance."""
    condition = (
        not user.has_perm("relaydomains.change_relaydomain") or
        domain.type != "relaydomain"
    )
    if condition:
        return {}
    return {"relaydomain": domain.relaydomain}


@receiver(admin_signals.extra_domain_qset_filters)
def extra_domain_entries(sender, domfilter, extrafilters, **kwargs):
    """Return extra queryset filters."""
    if domfilter is not None and domfilter and domfilter != "relaydomain":
        return {}
    if "srvfilter" in extrafilters and extrafilters["srvfilter"]:
        return {"relaydomain__service__name": extrafilters["srvfilter"]}
    return {}


@receiver(admin_signals.extra_domain_types)
def extra_domain_types(sender, **kwargs):
    """Declare the relay domain type."""
    return [("relaydomain", _("Relay domain"))]


@receiver(admin_signals.extra_domain_wizard_steps)
def extra_wizard_step(sender, **kwargs):
    """Return a step to configure the relay settings."""
    return [forms.RelayDomainWizardStep(
        "relay", forms.RelayDomainFormGeneral, _("Relay domain"),
        "relaydomains/relaydomain_form.html"
    )]


@receiver(admin_signals.get_domain_tags)
def get_tags_for_domain(sender, domain, **kwargs):
    """Return relay domain custom tags."""
    if domain.type != "relaydomain":
        return []
    return domain.relaydomain.tags


@receiver(admin_signals.import_object)
def get_import_func(sender, objtype, **kwargs):
    """Return function used to import objtype."""
    if objtype == "relaydomain":
        return lib.import_relaydomain
    return None
