from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from modoboa.lib import parameters
from modoboa.lib import exec_cmd, exec_as_vuser
import os

class Domain(models.Model):
    name = models.CharField(_('name'), max_length=100,
                            help_text=_("The domain name"))
    quota = models.IntegerField(help_text=_("Default quota in MB applied to mailboxes"))
    enabled = models.BooleanField(_('enabled'),
                                  help_text=_("Check to activate this domain"))

    class Meta:
        permissions = (
            ("view_domain", "View domain"),
            ("view_domains", "View domains"),
            )

    def create_dir(self):
        path = "%s/%s" % (parameters.get_admin("admin", "STORAGE_PATH"), self.name)
        return exec_as_vuser("mkdir -p %s" % path)

    def rename_dir(self, newname):
        stpath = parameters.get_admin("admin", "STORAGE_PATH")
        return exec_as_vuser("mv %s/%s %s/%s" \
                                 % (stpath, self.name, stpath, newname))

    def delete_dir(self):
        return exec_as_vuser("rm -r %s/%s" \
                                 % (parameters.get_admin("admin", "STORAGE_PATH"), 
                                    self.name))

    def __str__(self):
        return self.name

class Mailbox(models.Model):
    name = models.CharField(_('name'), max_length=100, 
                            help_text=_("First name and last name of mailbox owner"))
    address = models.CharField(_('address'), max_length=100,
                               help_text=_("Mailbox address (without the @domain.tld part)"))
    full_address = models.CharField(max_length=150)
    password = models.CharField(_('password'), max_length=100)
    quota = models.IntegerField()
    uid = models.IntegerField()
    gid = models.IntegerField()
    path = models.CharField(max_length=200)
    domain = models.ForeignKey(Domain)
    user = models.ForeignKey(User)
    path = models.CharField(max_length=255)

    class Meta:
        permissions = (
            ("view_mailboxes", "View mailboxes"),
            )

    def __init__(self, *args, **kwargs):
        super(Mailbox, self).__init__(*args, **kwargs)
        self.mbtype = parameters.get_admin("admin", "MAILBOX_TYPE")
        self.mdirroot = parameters.get_admin("admin", "MAILDIR_ROOT")

    def __str__(self):
        return "%s" % (self.address)

    def create_dir(self, domain):
        path = "%s/%s/%s" % (parameters.get_admin("admin", "STORAGE_PATH"),
                             domain.name, self.address)
        if os.path.exists(path):
            return True
        if not exec_as_vuser("mkdir -p %s" % path):
            return False
        if self.mbtype == "mbox":
            template = ["Inbox", "Drafts", "Sent", "Trash", "Junk"]
            for dir in template:
                exec_as_vuser("touch %s/%s" % (path, dir))
                    
            self.path = "%s/%s/Inbox" % (domain.name, self.address)
        else:
            template = [".Drafts/", ".Sent/", ".Trash/", ".Junk/"]
            for dir in template:
                for sdir in ["cur", "new", "tmp"]:
                    exec_as_vuser("mkdir -p %s/%s/%s/%s" \
                                      % (path, self.mdirroot, dir, sdir))
            self.path = "%s/%s/%s/" % (domain.name, self.address, self.mdirroot)
        return True

    def rename_dir(self, domain, newaddress):
        path = "%s/%s" % (parameters.get_admin("admin", "STORAGE_PATH"), domain)
        code = exec_as_vuser("mv %s/%s %s/%s" \
                                 % (path, self.address, path, newaddress))
        if code:
            self.path = "%s/%s/%s/" % (domain, newaddress, self.mdirroot)
        return code

    def delete_dir(self):
        return exec_as_vuser("rm -r %s/%s/%s" \
                                 % (parameters.get_admin("admin", "STORAGE_PATH"),
                                    self.domain.name, self.address))

class Alias(models.Model):
    address = models.CharField(_('address'), max_length=100,
                               help_text=_("The alias address (without the domain part)"))
    full_address = models.CharField(max_length=150)
    mboxes = models.ManyToManyField(Mailbox, verbose_name=_('mailboxes'),
                                    help_text=_("The mailboxes this alias points to"))
    enabled = models.BooleanField(_('enabled'),
                                  help_text=_("Check to activate this alias"))

    class Meta:
        permissions = (
            ("view_aliases", "View aliases"),
            )

