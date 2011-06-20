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
 * Dates (creation/modification)
 * Logs
 * Fetchmail table 

Mailboxes organization on the filesystem will be changed. PostfixAdmin
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
from django.conf import settings
from django.db.utils import ConnectionDoesNotExist
from django.db.models import Q
from django.contrib.auth.models import Group
import modoboa.admin.models as md_models
import models as pf_models
from modoboa.lib import exec_cmd
from modoboa.lib.emailutils import split_mailbox

def migrate_domain_aliases(domain, options):
    print "\tMigrating domain aliases"
    old_domain_aliases = pf_models.AliasDomain.objects.using(options._from).filter(target_domain=domain.name)
    for old_da in old_domain_aliases:
        new_da = md_models.DomainAlias()
        new_da.name = old_da.alias_domain
        new_da.target = old_da.target_domain
        new_da.enabled = new_da.active
        new_da.save(using=options.to)

def migrate_mailbox_aliases(domain, options):
    print "\tMigrating mailbox aliases"
    old_aliases = pf_models.Alias.objects.using(options._from).filter(domain=domain.name)
    for old_al in old_aliases:
        if old_al.address == old_al.goto:
            continue
        new_al = md_models.Alias()
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
                mb = md_models.Mailbox.objects.using(options.to).get(user__username=goto)
            except md_models.Mailbox.DoesNotExist:
                extmboxes += [goto]
            else:
                intmboxes += [mb]
        new_al.save(intmboxes, extmboxes, using=options.to)

def migrate_mailboxes(domain, options):
    print "\tMigrating mailboxes"
    old_mboxes = pf_models.Mailbox.objects.using(options._from).filter(domain=domain.name)
    for old_mb in old_mboxes:
        new_mb = md_models.Mailbox()
        new_mb.name = old_mb.name
        new_mb.address = old_mb.local_part
        new_mb.password = old_mb.password
        new_mb.domain = domain
        if old_mb.quota:
            new_mb.quota = old_mb.quota / 1024000
            
        new_mb.path = "%s/" % old_mb.local_part
        if options.rename_dirs:
            oldpath = os.path.join(options.mboxes_path, domain.name, old_mb.maildir)
            newpath = os.path.join(options.mboxes_path, domain.name, new_mb.path)
            code, output = exec_cmd("mv %s %s" % (oldpath, newpath))
            if code:
                print "Error: cannot rename mailbox directory\n%s" % output
                sys.exit(1)

        new_mb.save(using=options.to)
        

def migrate_domain(old_dom, options):
    print "Migrating domain %s" % old_dom.domain
    newdom = md_models.Domain()
    newdom.name = old_dom.domain
    newdom.enabled = old_dom.active
    newdom.quota = old_dom.maxquota
    newdom.save(using=options.to)
    migrate_mailboxes(newdom, options)
    migrate_mailbox_aliases(newdom, options)
    migrate_domain_aliases(newdom, options)

def migrate_admins(options):
    print "Migrating administrators"

    dagroup = Group.objects.using(options.to).get(name="DomainAdmins")
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
            mb = md_models.Mailbox.objects.using(options.to).get(user__username=old_admin.username)
        except md_models.Mailbox.DoesNotExist:
            try:
                domain = md_models.Domain.objects.using(options.to).get(name=domname)
            except md_models.Domain.DoesNotExist:
                print "Warning: skipping domain admin %s, domain not found" \
                    % old_admin.username
                continue
            mb = md_models.Mailbox()
            mb.address = local_part
            mb.domain = domain
            mb.name = local_part
            mb.enabled = old_admin.active
            mb.password = old_admin.password
            mb.save(using=options.to)            

        if creds.domain == "ALL":
            mb.user.is_superuser = True
        else:
            mb.user.groups.add(dagroup)
        mb.save(using=options.to)

def do_migration(options):
    pf_domains = pf_models.Domain.objects.using(options._from).all()
    for olddom in pf_domains:
        if olddom.domain == "ALL":
            continue
        migrate_domain(olddom, options)
    migrate_admins(options)

if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-f", "--from", dest="_from", default="pfxadmin",
                      help="Name of postfixadmin db connection declared in settings.py")
    parser.add_option("-t", "--to", default="modoboa",
                      help="Name of the Modoboa db connection declared in settings.py")
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
        
    

    
