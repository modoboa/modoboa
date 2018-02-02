# -*- coding: utf-8 -*-

"""Management command to check and fix known problems."""

from __future__ import print_function, unicode_literals

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.encoding import smart_str

from modoboa.admin import models
from modoboa.core.models import User
from modoboa.lib.permissions import get_object_owner, grant_access_to_object

known_problems = []


def known_problem(func):
    """Simple decorator to register a known problem."""
    known_problems.append(func)
    return func


def log(message, quiet=False, **options):
    if not quiet:
        print(message)


def fix_owner(qs, dry_run=False, **options):
    """Fix ownership for orphan objects."""
    model = qs.model
    for obj in qs:
        kw = {"cls": model.__name__, "obj": obj}
        if get_object_owner(obj) is not None:
            continue
        if dry_run:
            log("  {cls} {obj} has no owner".format(**kw), **options)
            continue
        if isinstance(obj, User):
            admin = User.objects.filter(
                is_superuser=True, is_active=True).first()
        elif isinstance(obj, models.Domain):
            admin = obj.admins.first()
        elif isinstance(obj, models.DomainAlias):
            admin = obj.target.admins.first()
        else:
            admin = obj.domain.admins.first()
        if not admin:
            # Fallback: use the first superuser found
            admin = User.objects.filter(
                is_superuser=True, is_active=True).first()
        grant_access_to_object(admin, obj, is_owner=True)
        kw["admin"] = admin
        log("  {cls} {obj} is now owned by {admin}".format(**kw),
            **options)


@known_problem
def sometimes_objects_have_no_owner(**options):
    """Sometime objects have no owner."""
    owned_models = (
        User.objects.all(),
        models.Domain.objects.all(),
        models.DomainAlias.objects.all(),
        models.Alias.objects.filter(domain__isnull=False),
        models.Mailbox.objects.filter(domain__isnull=False),
    )
    for qs in owned_models:
        fix_owner(qs, **options)


@known_problem
def sometimes_mailbox_have_no_alias(**options):
    """Sometime mailboxes have no alias."""
    alias_created = 0
    recipient_created = 0
    for instance in models.Mailbox.objects.select_related("domain").all():
        alias, created = models.Alias.objects.get_or_create(
            address=instance.full_address,
            domain=instance.domain,
            internal=True)
        if created:
            alias_created += 1
            log("Alias {0} created".format(alias), **options)
        recipient, created = models.AliasRecipient.objects.get_or_create(
            alias=alias,
            address=instance.full_address,
            r_mailbox=instance)
        if created:
            recipient_created += 1
            log("AliasRecipient {0} created".format(recipient), **options)
    if alias_created or recipient_created:
        log("{0} alias created. {1} alias recipient created".format(
            alias_created, recipient_created), **options)


class Repair(BaseCommand):
    """Command class."""

    help = "Check and fix known problems."  # NOQA:A003

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
        # Load known problems from extensions.
        for ext in settings.MODOBOA_APPS:
            try:
                __import__(
                    ext, locals(), globals(),
                    [smart_str("known_problems")]
                )
            except ImportError:
                pass
        for func in known_problems:
            title = func.__doc__.strip()
            log("", **options)
            log("Checking for... {}...".format(title), **options)
            func(**options)
