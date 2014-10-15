# coding: utf-8

"""Automatic postfixadmin to Modoboa migration
===========================================

This script provides an easy way to migrate an existing postfixadmin
database to a Modoboa one.

As the two products do not share the same schema, some information
will be lost on the new database. Here is the list:
 * Description, transport and backup MX for domains
 * Logs
 * Fetchmail table

Domain administrators that manage more than one domain will not be
completly restored. They will only be administrator of the domain that
corresponds to their username.

Vacation messages will not be migrated by this script. Users will have
to define new messages by using Modoboa's autoreply plugin. (if
activated)

One last point about passwords. PostfixAdmin uses different hash
algorithms to store passwords so this script does not modify
them. They are copied "as is" in the new database. In order to use
them, use the ``--passwords-scheme`` to tell Modoboa which scheme was
used by PostfixAdmin.

.. note::

   Actually, it appears that the ``crypt`` scheme is compatible with
   PostfixAdmin ``md5crypt`` algorithm...

"""
from optparse import make_option
import re

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

import modoboa.core.models as core_models
import modoboa.extensions.admin.models as admin_models
from modoboa.lib.emailutils import split_mailbox
from modoboa.extensions.admin import grant_access_to_all_objects

from modoboa.tools.pfxadmin_migrate import models as pf_models


def set_account_password(account, password, scheme):
    """Correclty format the password before storing it.

    It seems postfixadmin sometimes prepend the scheme... but not
    always :p

    """
    if re.search(r"\{[\w-]+\}", password):
        account.password = password
    else:
        account.password = "{%s}%s" % (scheme.upper(), password)


class Command(BaseCommand):

    """Migration from postfixadmin."""

    help = "This command eases the migration from a postfixadmin database."
    option_list = BaseCommand.option_list + (
        make_option(
            "-f", "--from", dest="_from", default="pfxadmin",
            help="Name of postfixadmin db connection declared in settings.py"
            "(default is pfxadmin)"
        ),
        make_option(
            "-t", "--to", dest="_to", default="default",
            help="Name of the Modoboa db connection declared in settings.py"
            " (default is default)"
        ),
        make_option(
            "-s", "--passwords-scheme", default="crypt",
            help="Scheme used to crypt user passwords"
        )
    )

    def _migrate_dates(self, oldobj):
        """Creates a new ObjectDates instance.

        Due to Django limitations, we only retrieve the creation date. The
        modification date will be set to 'now' because the corresponding
        field in Modoboa's schema has the 'auto_now' attribute to True.
        (see https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.DateField).

        :param oldobj: the PostfixAdmin record which is beeing migrated.
        """
        dates = admin_models.base.ObjectDates()
        dates.save()

        dates.creation = oldobj.created
        dates.save()
        return dates

    def _migrate_domain_aliases(self, domain, options, creator):
        """Migrate aliases of a single domain."""
        print "\tMigrating domain aliases"
        old_domain_aliases = pf_models.AliasDomain.objects.using(
            options["_from"]
        ).filter(target_domain=domain.name)
        for old_da in old_domain_aliases:
            try:
                target_domain = admin_models.Domain.objects \
                    .using(options["_to"]).get(name=old_da.target_domain)
                new_da = admin_models.DomainAlias()
                new_da.name = old_da.alias_domain
                new_da.target = target_domain
                new_da.enabled = old_da.active
                new_da.dates = self._migrate_dates(old_da)
                new_da.save(using=options["_to"])
                new_da.post_create(creator)
            except core_models.Domain.DoesNotExist:
                print ("Warning: target domain %s does not exists, "
                       "not creating alias domain %s"
                       % old_da.target_domain, old_da.alias_domain)
                continue

    def _migrate_mailbox_aliases(self, domain, options, creator):
        """Migrate mailbox aliases of a single domain."""
        print "\tMigrating mailbox aliases"
        old_aliases = pf_models.Alias.objects \
            .using(options["_from"]).filter(domain=domain.name)
        for old_al in old_aliases:
            if old_al.address == old_al.goto:
                continue
            new_al = admin_models.Alias()
            local_part, tmp = split_mailbox(old_al.address)
            if local_part is None or not len(local_part):
                if tmp is None or not len(tmp):
                    print (
                        "Warning: skipping alias %s (cannot retrieve local "
                        "part). You will need to recreate it manually."
                        % old_al.address
                    )
                    continue
                new_al.address = "*"
            else:
                new_al.address = local_part
            new_al.domain = domain
            new_al.enabled = old_al.active
            extmboxes = []
            intmboxes = []
            for goto in old_al.goto.split(","):
                try:
                    mb = admin_models.Mailbox.objects \
                        .using(options["_to"]).get(user__username=goto)
                except admin_models.Mailbox.DoesNotExist:
                    extmboxes += [goto]
                else:
                    intmboxes += [mb]
            new_al.dates = self._migrate_dates(old_al)
            new_al.save(
                int_rcpts=intmboxes, ext_rcpts=extmboxes, creator=creator,
                using=options["_to"]
            )

    def _migrate_mailboxes(self, domain, options, creator):
        """Migrate mailboxes of a single domain."""
        print "\tMigrating mailboxes"
        old_mboxes = pf_models.Mailbox.objects \
            .using(options["_from"]).filter(domain=domain.name)
        for old_mb in old_mboxes:
            new_user = core_models.User()
            new_user.username = old_mb.username
            new_user.first_name = old_mb.name.partition(' ')[0]
            new_user.last_name = old_mb.name.partition(' ')[2]
            new_user.email = old_mb.username
            new_user.is_active = old_mb.active
            new_user.date_joined = old_mb.created
            set_account_password(
                new_user, old_mb.password, options["passwords_scheme"])
            new_user.dates = self._migrate_dates(old_mb)
            new_user.save(creator=creator, using=options["_to"])
            new_user.set_role("SimpleUsers")

            new_mb = admin_models.Mailbox()
            new_mb.user = new_user
            new_mb.address = old_mb.local_part
            new_mb.domain = domain
            new_mb.dates = self._migrate_dates(old_mb)
            new_mb.set_quota(old_mb.quota / 1024000, override_rules=True)
            new_mb.save(creator=creator, using=options["_to"])

    def _migrate_domain(self, pf_domain, options, creator):
        """Single domain migration."""
        print "\nMigrating domain %s" % pf_domain.domain
        newdom = admin_models.Domain()
        newdom.name = pf_domain.domain
        newdom.enabled = pf_domain.active
        newdom.quota = pf_domain.maxquota
        newdom.dates = self._migrate_dates(pf_domain)
        newdom.save(creator=creator, using=options["_to"])
        self._migrate_domain_aliases(newdom, options, creator)
        self._migrate_mailboxes(newdom, options, creator)
        self._migrate_mailbox_aliases(newdom, options, creator)
        self._migrate_admins(options, creator, pf_domain, newdom)

    def _migrate_admins(self, options, creator, pf_domain, newdom=None):
        """Administrators migration.

        :param pf_domain: The ``pf_models.Domain`` to get the admins to migrate.
        :param newdom:    If None the admins will not be linked to any domain
                          and they will be SuperAdmins. Otherwise link them to
                          this domain and make them DomainAdmins.
        """

        if newdom is None:
            print "\nMigrating super administrators"
        else:
            print "\tMigrating administrators"

        dagroup = Group.objects.using(options["_to"]).get(name="DomainAdmins")
        for old_admin in pf_domain.admins.all():
            if newdom is None:
                print "\tMigrating %s" % old_admin.username

            # In postfixadmin, it's possible to have an admin account
            # and a user account with the same username but they are
            # completely different entities, so they do not have a
            # common password. In Modoboa this does not makes sense, so
            # we actually merge these two entities into a single user
            # if both are found. Question is, which password should we
            # use?. The admin password is used to be on the secure
            # side.
            try:
                user = core_models.User.objects \
                    .using(options["_to"]).get(username=old_admin.username)

                if "SimpleUsers" == user.group:
                    print (
                        "Warning: Found an admin account with the same "
                        "username as normal user '%s'. The existing user will "
                        "be promoted to admin and it's password changed to the "
                        "admin's account password. " % user.username
                    )

            except core_models.User.DoesNotExist:
                user = core_models.User()
                user.username = old_admin.username
                user.email = old_admin.username
                user.is_active = old_admin.active
                user.save(creator=creator, using=options["_to"])

            user.date_joined = old_admin.modified
            set_account_password(
                user, old_admin.password, options["passwords_scheme"])

            if newdom is None:
                grant_access_to_all_objects(user, "SuperAdmins")
                user.is_superuser = True
            else:
                user.groups.add(dagroup)
                newdom.add_admin(user)

            user.save(using=options["_to"])

    def _do_migration(self, options, creator_username='admin'):
        """Run the complete migration."""
        pf_domains = pf_models.Domain.objects.using(
            options["_from"]).exclude(domain='ALL')
        creator = core_models.User.objects.using(options["_to"]).get(
            username=creator_username)
        for pf_domain in pf_domains:

            try:
                # Skip this domain if it's an alias
                is_domain_alias = pf_models.AliasDomain.objects \
                    .using(options["_from"]).get(alias_domain=pf_domain.domain)
                print "Info: %s looks like an alias domain, skipping it" \
                    % pf_domain.domain
                continue
            except pf_models.AliasDomain.DoesNotExist:
                self._migrate_domain(pf_domain, options, creator)

        # Handle the ALL domain
        pf_domain = pf_models.Domain.objects.using(
            options["_from"]).get(domain='ALL')
        self._migrate_admins(options, creator, pf_domain)

    def handle(self, *args, **options):
        """Command entry point."""
        with transaction.commit_on_success():
            self._do_migration(options)
