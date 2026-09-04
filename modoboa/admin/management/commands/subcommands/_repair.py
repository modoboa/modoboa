"""Management command to check and fix known problems."""

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils.encoding import smart_str


from modoboa.admin import models
from modoboa.core.models import ObjectAccess, User
from modoboa.lib.permissions import grant_access_to_object

known_problems = []


def known_problem(func):
    """Simple decorator to register a known problem."""
    known_problems.append(func)
    return func


def log(message, quiet=False, **options):
    if not quiet:
        print(message)


def orphan_objects(qs):
    """Restrict qs to objects without owner.

    The lookup is pushed down to the database so that a single query is
    needed, whatever the number of objects in qs.
    """
    ct = ContentType.objects.get_for_model(qs.model)
    owner = ObjectAccess.objects.filter(
        content_type=ct, object_id=OuterRef("pk"), is_owner=True
    )
    return qs.filter(~Exists(owner))


def fix_owner(qs, dry_run=False, **options):
    """Fix ownership for orphan objects."""
    model = qs.model
    superusers = None
    default_admin = None
    for obj in orphan_objects(qs):
        kw = {"cls": model.__name__, "obj": obj}
        if dry_run:
            log("  {cls} {obj} has no owner".format(**kw), **options)
            continue
        if superusers is None:
            # Fetched once for the whole queryset instead of once per
            # object, and reused by grant_access_to_object().
            superusers = list(User.objects.filter(is_superuser=True).order_by("pk"))
            default_admin = next((su for su in superusers if su.is_active), None)
        if isinstance(obj, User):
            admin = default_admin
        elif isinstance(obj, models.Domain):
            admin = obj.admins.first()
        elif isinstance(obj, models.DomainAlias):
            admin = obj.target.admins.first()
        else:
            admin = obj.domain.admins.first()
        if not admin:
            # Fallback: use the first superuser found
            admin = default_admin
        grant_access_to_object(admin, obj, is_owner=True, superusers=superusers)
        kw["admin"] = admin
        log("  {cls} {obj} is now owned by {admin}".format(**kw), **options)


@known_problem
def sometimes_objects_have_no_owner(**options):
    """Sometime objects have no owner."""
    owned_models = (
        User.objects.all(),
        models.Domain.objects.all(),
        models.DomainAlias.objects.select_related("target"),
        models.Alias.objects.select_related("domain").filter(
            internal=False, domain__isnull=False
        ),
        models.Mailbox.objects.select_related("domain").filter(domain__isnull=False),
    )
    for qs in owned_models:
        fix_owner(qs, **options)


@known_problem
def sometimes_mailbox_have_no_alias(**options):
    """Sometime mailboxes have no alias."""
    alias_created = 0
    recipient_created = 0
    # Load what already exists first: the vast majority of mailboxes have
    # nothing to fix and we don't want to query the database for each of them.
    known_aliases = {
        (address, domain_id): pk
        for pk, address, domain_id in models.Alias.objects.filter(
            internal=True
        ).values_list("pk", "address", "domain_id")
    }
    known_recipients = set(
        models.AliasRecipient.objects.filter(
            alias__internal=True, r_mailbox__isnull=False
        ).values_list("alias_id", "r_mailbox_id")
    )
    mailboxes = models.Mailbox.objects.values_list(
        "pk", "address", "domain_id", "domain__name"
    )
    for mb_id, local_part, domain_id, domain_name in mailboxes.iterator():
        full_address = f"{local_part}@{domain_name}"
        alias_id = known_aliases.get((full_address, domain_id))
        if alias_id is None:
            alias = models.Alias.objects.create(
                address=full_address, domain_id=domain_id, internal=True
            )
            alias_id = alias.pk
            known_aliases[(full_address, domain_id)] = alias_id
            alias_created += 1
            log(f"Alias {alias} created", **options)
        if (alias_id, mb_id) not in known_recipients:
            recipient = models.AliasRecipient.objects.create(
                alias_id=alias_id, address=full_address, r_mailbox_id=mb_id
            )
            known_recipients.add((alias_id, mb_id))
            recipient_created += 1
            log(f"AliasRecipient {recipient} created", **options)
    if alias_created or recipient_created:
        log(
            f"{alias_created} alias created. {recipient_created} alias recipient created",
            **options,
        )


class Repair(BaseCommand):
    """Command class."""

    help = "Check and fix known problems."  # NOQA:A003

    def add_arguments(self, parser):
        """Add extra arguments to command."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="List known problems without fixing them.",
        )
        parser.add_argument(
            "--quiet", action="store_true", default=False, help="Quiet mode."
        )

    def handle(self, *args, **options):
        """Command entry point."""
        # Load known problems from extensions.
        for ext in settings.MODOBOA_APPS:
            try:
                __import__(ext, locals(), globals(), [smart_str("known_problems")])
            except ImportError:
                pass
        for func in known_problems:
            title = func.__doc__.strip()
            log("", **options)
            log(f"Checking for... {title}...", **options)
            # A single transaction per check: the database commits once
            # instead of once per fixed object, and a failing check leaves
            # nothing half repaired behind.
            with transaction.atomic():
                func(**options)
