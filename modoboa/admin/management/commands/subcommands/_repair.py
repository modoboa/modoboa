"""Management command to check and fix known problems."""
from django.core.management.base import BaseCommand

from modoboa.lib.permissions import grant_access_to_object
from modoboa.lib.permissions import get_object_owner

from modoboa.core.models import User
from modoboa.admin import models

try:
    from modoboa_postfix_autoreply.models import ARmessage
except ImportError:
    ARmessage = None


known_problems = []


def known_problem(func):
    known_problems.append(func.__name__)
    return func


class Repair(BaseCommand):
    """Command class."""

    help = "Check and fix known problems."

    def add_arguments(self, parser):
        """Add extra arguments to command."""
        parser.add_argument(
            "--dry-run", action="store_true", default=False,
            help="List known problems without fixing them.")
        parser.add_argument(
            "--quiet", action="store_true", default=False,
            help="Quiet mode.")

    def handle(self, *args, **options):
        """Command entry point."""
        for problem in known_problems:
            func = getattr(self, problem)
            title = func.__doc__.strip()
            self.log("", **options)
            self.log("Checking for... {}...".format(title), **options)
            func(**options)

    def log(self, message, quiet=False, **options):
        if not quiet:
            print(message)

    def fix_owner(self, qs, dry_run=False, **options):
        model = qs.model
        for obj in qs:
            kw = dict(
                cls=model.__name__,
                obj=obj
            )
            if get_object_owner(obj) is None:
                if dry_run:
                    self.log(
                        "  {cls} {obj} has no owner".format(**kw),
                        **options)
                else:
                    if isinstance(obj, User):
                        admin = User.objects.filter(is_superuser=True,
                                                    is_active=True).first()
                    elif isinstance(obj, models.Domain):
                        admin = obj.admins.first()
                    elif isinstance(obj, models.DomainAlias):
                        admin = obj.target.admins.first()
                    else:
                        admin = obj.domain.admins.first()
                    if not admin:
                        # domain has no admin. use the first superuser found
                        admin = User.objects.filter(is_superuser=True,
                                                    is_active=True).first()
                    grant_access_to_object(admin, obj, is_owner=True)
                    kw['admin'] = admin
                    self.log(
                        "  {cls} {obj} is now owned by {admin}".format(**kw),
                        **options)

    @known_problem
    def sometimes_objects_have_no_owner(self, **options):
        """Sometime objects have no owner"""
        owned_models = (
            User.objects.all(),
            models.Domain.objects.all(),
            models.DomainAlias.objects.all(),
            models.Alias.objects.filter(domain__isnull=False),
            models.Mailbox.objects.filter(domain__isnull=False),
        )
        for qs in owned_models:
            self.fix_owner(qs, **options)

    @known_problem
    def ensure_autoreplies_recipents_are_valids(self, **options):
        """Sometime autoreply alias exists when ARmessage is not enabled"""
        if ARmessage is None:
            return
        deleted = 0
        qs = models.AliasRecipient.objects.filter(
            address__contains='@autoreply.')
        for alias in qs:
            address, domain = alias.alias.address.split('@')
            arqs = ARmessage.objects.filter(
                mbox__address=address,
                mbox__domain__name=domain)
            if not arqs.count():
                self.log('Delete {0} (No AR found)'.format(alias))
                deleted += 1
            else:
                for ar in arqs:
                    if not ar.enabled:
                        self.log('Delete {0} (AR disabled)'.format(alias))
                        alias.delete()
                        deleted += 1
        if deleted:
            self.log('{0} alias recipient deleted'.format(deleted))

    @known_problem
    def sometimes_mailbox_have_no_alias(self, **options):
        """Sometime mailboxes have no alias"""
        alias_created = 0
        recipient_created = 0
        for instance in models.Mailbox.objects.all():
            alias, created = models.Alias.objects.get_or_create(
                address=instance.full_address,
                domain=instance.domain,
                internal=True)
            if created:
                alias_created += 1
                self.log('Alias {0} created'.format(alias))
            recipient, created = models.AliasRecipient.objects.get_or_create(
                alias=alias,
                address=instance.full_address,
                r_mailbox=instance)
            if created:
                recipient_created += 1
                self.log('AliasRecipient {0} created'.format(recipient))
        if alias_created or recipient_created:
            self.log('{0} alias created. {1} alias recipient created'.format(
                alias_created, recipient_created))
