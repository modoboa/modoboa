"""Admin system checks."""

from django.core.checks import Tags, Warning, register
from django.db.utils import OperationalError, ProgrammingError
from django.utils.translation import gettext as _

REPAIR_HINT = _("Run `python manage.py modo repair --dry-run` for details.")


@register(Tags.database)
def check_domain_namespace(app_configs, databases=None, **kwargs):
    """Report inconsistencies between domains and domain aliases.

    They can have been introduced by previous versions. Nothing is
    fixed automatically since a record may belong to a legitimate
    tenant.
    """
    if not databases or "default" not in databases:
        return []
    from .lib import find_domainalias_inconsistencies

    try:
        collisions, orphans, wrong_routes = find_domainalias_inconsistencies()
    except (ProgrammingError, OperationalError):
        # This is probably a fresh install...
        return []
    msgs = []
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
    if orphans:
        msgs.append(
            Warning(
                _(
                    "Internal aliases generated for domain aliases are orphaned "
                    "or use the name of a domain: {}"
                ).format(", ".join(f"@{name}" for name in sorted(orphans))),
                hint=REPAIR_HINT,
                id="modoboa.admin.W002",
            )
        )
    if wrong_routes:
        msgs.append(
            Warning(
                _(
                    "Internal aliases generated for domain aliases are missing "
                    "or do not point to their target: {}"
                ).format(", ".join(f"@{name}" for name in sorted(wrong_routes))),
                hint=REPAIR_HINT,
                id="modoboa.admin.W003",
            )
        )
    return msgs
