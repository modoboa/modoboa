"""Management command to check and fix known problems."""
from django.core.management.base import BaseCommand

from modoboa.lib.permissions import grant_access_to_object
from modoboa.lib.permissions import get_object_owner

from modoboa.core.models import User
from modoboa.admin import models

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
            title = func.__name__.capitalize().replace("_", " ")
            self.log("", **options)
            self.log("Checking for... {}...".format(title), **options)
            func(**options)

    def log(self, message, quiet=False, **options):
        if not quiet:
            print(message)

    def fix_owner(self, model, dry_run=False, **options):
        for obj in model.objects.all():
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
        owned_models = (
            User,
            models.Domain,
            models.Mailbox,
            models.Alias,
            models.DomainAlias
        )
        for model in owned_models:
            self.fix_owner(model, **options)
