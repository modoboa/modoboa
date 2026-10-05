"""Admin system checks."""

from django.core.checks import Tags, Warning, register
from django.db.utils import OperationalError, ProgrammingError
from django.utils.translation import gettext as _


@register(Tags.database)
def check_domain_namespace(app_configs, databases=None, **kwargs):
    """Report inconsistencies between domains and domain aliases.

    They can have been introduced by previous versions. Nothing is
    fixed automatically since a record may belong to a legitimate
    tenant.
    """
    if not databases or "default" not in databases:
        return []
    from .models import Alias, Domain, DomainAlias

    try:
        domain_names = set(Domain.objects.values_list("name", flat=True))
        domain_alias_names = set(DomainAlias.objects.values_list("name", flat=True))
        generated_names = {
            address[1:]
            for address in Alias.objects.filter(
                address__startswith="@", internal=True, domain__isnull=True
            ).values_list("address", flat=True)
        }
    except (ProgrammingError, OperationalError):
        # This is probably a fresh install...
        return []
    msgs = []
    collisions = domain_names & domain_alias_names
    if collisions:
        msgs.append(
            Warning(
                _("Domain aliases using the name of a domain: {}").format(
                    ", ".join(sorted(collisions))
                ),
                hint=_(
                    "Check who owns these domain aliases, then rename or "
                    "delete them."
                ),
                id="modoboa.admin.W001",
            )
        )
    stale = (generated_names - domain_alias_names) | (generated_names & domain_names)
    if stale:
        msgs.append(
            Warning(
                _(
                    "Internal aliases generated for domain aliases are orphaned "
                    "or use the name of a domain: {}"
                ).format(", ".join(f"@{name}" for name in sorted(stale))),
                hint=_(
                    "Check these internal aliases and their recipients, then "
                    "delete the ones that do not match a domain alias."
                ),
                id="modoboa.admin.W002",
            )
        )
    return msgs
