#!/usr/bin/env python
# coding: utf-8

"""
Automatic postfixadmin to Modoboa migration
===========================================

This script provides an easy way to migrate an existing postfixadmin
database to a Modoboa one.

As the two products do not share the same schema, some informations
will be lost on the new database. Here is the list:
 * Description, transport and backup MX for domains
 * Logs
 * Fetchmail table

Mailboxes organisation on the filesystem will change. PostfixAdmin
uses the following layout::

  <topdir>/domain.tld/user@domain.tld/

Whereas Modoboa uses the following::

  <topdir>/domain.tld/user/

To rename directories, you'll need the appropriate permissions.

Domain administrators that manage more than one domain will not be
completly restored. They will only be administrator of the domain that
corresponds to their username.

Vacation messages will not be migrated by this script. Users will have
to define new messages by using Modoboa's autoreply plugin. (if
activated)

One last point about passwords. PostfixAdmin uses different hash
algorithms to store passwords so this script does not modify
them. They are copied "as is" is the new database. In order to use
them, you'll have to adapt the ``PASSWORD_SCHEME`` parameter in the
admin. panel. Currently, it appears that the ``crypt`` scheme is
compatible with PostfixAdmin ``md5crypt`` algorithm...

"""
import os
import sys
from django.db import transaction
from django.db.utils import ConnectionDoesNotExist
from django.db.models import Q
from django.contrib.auth.models import Group
import modoboa.extensions.admin.models as admin_models
import modoboa.core.models as core_models
import models as pf_models
from modoboa.lib.sysutils import exec_cmd
from modoboa.lib.emailutils import split_mailbox

def migrate_dates(oldobj):
    """Creates a new ObjectDates instance

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

def migrate_domain_aliases(domain, options, creator):
    print "\tMigrating domain aliases"
    old_domain_aliases = pf_models.AliasDomain.objects.using(options._from).filter(target_domain=domain.name)
    for old_da in old_domain_aliases:
        try:
            target_domain = admin_models.Domain.objects.using(options._to).get(name=old_da.target_domain)
            new_da = admin_models.DomainAlias()
            new_da.name = old_da.alias_domain
            new_da.target = target_domain
            new_da.enabled = old_da.active
            new_da.dates = migrate_dates(old_da)
            new_da.save(using=options._to)
            new_da.post_create(creator)
        except core_models.Domain.DoesNotExist as e:
            print "Warning: target domain %s does not exists, not creating alias domain %s" \
                % old_da.target_domain, old_da.alias_domain
            continue

def migrate_mailbox_aliases(domain, options, creator):
    print "\tMigrating mailbox aliases"
    old_aliases = pf_models.Alias.objects.using(options._from).filter(domain=domain.name)
    for old_al in old_aliases:
        if old_al.address == old_al.goto:
            continue
        new_al = admin_models.Alias()
        local_part, tmp = split_mailbox(old_al.address)
        if local_part is None or not len(local_part):
            if tmp is None or not len(tmp):
                print """Warning: skipping alias %s (cannot retrieve local part).
You will need to recreate it manually.
""" % old_al.address
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
                mb = admin_models.Mailbox.objects.using(options._to).get(user__username=goto)
            except admin_models.Mailbox.DoesNotExist:
                extmboxes += [goto]
            else:
                intmboxes += [mb]
        new_al.dates = migrate_dates(old_al)
        new_al.save(int_rcpts=intmboxes, ext_rcpts=extmboxes, creator=creator, using=options._to)

def migrate_mailboxes(domain, options, creator):
    print "\tMigrating mailboxes"
    old_mboxes = pf_models.Mailbox.objects.using(options._from).filter(domain=domain.name)
    for old_mb in old_mboxes:
        new_user = core_models.User()
        new_user.username = old_mb.username
        new_user.first_name = old_mb.name.partition(' ')[0]
        new_user.last_name = old_mb.name.partition(' ')[2]
        new_user.email = old_mb.username
        new_user.is_active = old_mb.active
        new_user.date_joined = old_mb.created
        new_user.password = old_mb.password
        new_user.dates = migrate_dates(old_mb)
        new_user.save(creator=creator, using=options._to)
        new_user.set_role("SimpleUsers")

        new_mb = admin_models.Mailbox()
        new_mb.user = new_user
        new_mb.address = old_mb.local_part
        new_mb.domain = domain
        new_mb.dates = migrate_dates(old_mb)
        if old_mb.quota:
            new_mb.quota = old_mb.quota / 1024000
        else:
            new_mb.quota = 0

        if options.rename_dirs:
            oldpath = os.path.join(options.mboxes_path, domain.name, old_mb.maildir)
            newpath = os.path.join(options.mboxes_path, domain.name, new_mb.path)
            code, output = exec_cmd("mv %s %s" % (oldpath, newpath))
            if code:
                print "Error: cannot rename mailbox directory\n%s" % output
                sys.exit(1)

        new_mb.save(creator=creator, using=options._to)

def migrate_domain(old_dom, options, creator):
    print "Migrating domain %s" % old_dom.domain
    newdom = admin_models.Domain()
    newdom.name = old_dom.domain
    newdom.enabled = old_dom.active
    newdom.quota = old_dom.maxquota
    newdom.dates = migrate_dates(old_dom)
    newdom.save(creator=creator, using=options._to)
    migrate_mailboxes(newdom, options, creator)
    migrate_mailbox_aliases(newdom, options, creator)
    migrate_domain_aliases(newdom, options, creator)

def migrate_admins(options, creator):
    print "Migrating administrators"

    dagroup = Group.objects.using(options._to).get(name="DomainAdmins")
    for old_admin in pf_models.Admin.objects.using(options._from).all():
        local_part, domname = split_mailbox(old_admin.username)
        try:
            query = Q(username=old_admin.username) & \
                (Q(domain="ALL") | Q(domain=domname))
            creds = pf_models.DomainAdmins.objects.using(options._from).get(query)
        except pf_models.DomainAdmins.DoesNotExist:
            print "Warning: skipping useless admin %s" % (old_admin.username)
            continue
        try:
            user = core_models.User.objects.using(options._to).get(username=old_admin.username)
        except core_models.User.DoesNotExist:
            try:
                domain = admin_models.Domain.objects.using(options._to).get(name=domname)
            except admin_models.Domain.DoesNotExist:
                print "Warning: skipping domain admin %s, domain not found" \
                    % old_admin.username
                continue
            user = core_models.User()
            user.username = old_admin.username
            user.email = old_admin.username
            user.password = old_admin.password
            user.is_active = old_admin.active
            user.save(creator=creator, using=options._to)

        user.date_joined = old_admin.modified
        if creds.domain == "ALL":
            user.is_superuser = True
        else:
            user.groups.add(dagroup)
        user.save(using=options._to)

@transaction.commit_on_success
def do_migration(options, creator_username='admin'):
    pf_domains = pf_models.Domain.objects.using(options._from).all()
    creator = core_models.User.objects.using(options._to).get(username=creator_username)
    for pf_domain in pf_domains:

        if pf_domain.domain == "ALL":
            continue

        try:
            #Skip this domain if it's an alias
            is_domain_alias = pf_models.AliasDomain.objects.using(options._from).get(alias_domain=pf_domain.domain)
            print "Info: %s looks like an alias domain, skipping it" \
                    % pf_domain.domain
            continue
        except pf_models.AliasDomain.DoesNotExist:
            migrate_domain(pf_domain, options, creator)
            migrate_admins(options, creator)

if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-f", "--from", dest="_from", default="pfxadmin",
                      help="Name of postfixadmin db connection declared in settings.py (default is pfxadmin)")
    parser.add_option("-t", "--to", dest="_to", default="default",
                      help="Name of the Modoboa db connection declared in settings.py (default is default)")
    parser.add_option("-r", "--rename-dirs", action="store_true",
                      help="Rename mailbox directories (default is no)")
    parser.add_option("-p", "--mboxes-path", default=None,
                      help="Path where directories are stored on the filesystem (used only if --rename-dirs)")

    options, args = parser.parse_args()

    if options.rename_dirs and options.mboxes_path is None:
        print "Error: you must provide the --mboxes-path option"
        sys.exit(1)

    try:
        do_migration(options)
    except ConnectionDoesNotExist, e:
        print e
