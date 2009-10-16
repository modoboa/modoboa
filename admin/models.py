from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from mailng.lib import exec_pipe, exec_as_vuser
import os

class Domain(models.Model):
    name = models.CharField(_('name'), max_length=100)
    quota = models.IntegerField()
    enabled = models.BooleanField(_('enabled'))

    class Meta:
        permissions = (
            ("view_domain", "View domain"),
            ("view_domains", "View domains"),
            )

    def create_dir(self):
        path = "%s/%s" % (settings.STORAGE_PATH, self.name)
        return exec_as_vuser("mkdir -p %s" % path)

    def rename_dir(self, newname):
        return exec_as_vuser("mv %s/%s %s/%s" \
                                 % (settings.STORAGE_PATH, self.name,
                                    settings.STORAGE_PATH, newname))

    def delete_dir(self):
        return exec_as_vuser("rm -r %s/%s" \
                                 % (settings.STORAGE_PATH, self.name))

    def __str__(self):
        return self.name

class Mailbox(models.Model):
    name = models.CharField(_('name'), max_length=100)
    address = models.CharField(_('address'), max_length=100)
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
        try:
            self.mbtype = getattr(settings, "MAILBOX_TYPE")
        except AttributeError:
            self.mbtype = "maildir"
        try:
            self.mdirroot = getattr(settings, "MAILDIR_ROOT")
        except AttributeError:
            self.mdirroot = ".maildir"

    def __str__(self):
        return "%s" % (self.address)

    def create_dir(self, domain):
        path = "%s/%s/%s" % (settings.STORAGE_PATH, domain.name, self.address)
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
        path = "%s/%s" % (settings.STORAGE_PATH, domain)
        code = exec_as_vuser("mv %s/%s %s/%s" \
                                 % (path, self.address, path, newaddress))
        if code:
            self.path = "%s/%s/%s/" % (domain, newaddress, self.mdirroot)
        return code

    def delete_dir(self):
        return exec_as_vuser("rm -r %s/%s/%s" \
                                     % (settings.STORAGE_PATH,
                                        self.domain.name, self.address))

class Alias(models.Model):
    address = models.CharField(_('address'), max_length=100)
    full_address = models.CharField(max_length=150)
    mbox = models.ForeignKey(Mailbox, verbose_name=_('mailbox'))
    enabled = models.BooleanField(_('enabled'))

    class Meta:
        permissions = (
            ("view_aliases", "View aliases"),
            )
