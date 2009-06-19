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
        return exec_as_vuser("mkdir %s" % path)

    def rename_dir(self, newname):
        code, output = exec_pipe("sudo -u %s mv %s/%s %s/%s" \
                                     % (settings.VIRTUAL_UID, 
                                        settings.STORAGE_PATH, self.name,
                                        settings.STORAGE_PATH, newname))
        if code:
            os.system("echo '%s' >> /tmp/vmail.log" % output)
            return False
        return True

    def delete_dir(self):
        code, output = exec_pipe("sudo -u %s rm -r %s/%s" \
                                     % (settings.VIRTUAL_UID, 
                                        settings.STORAGE_PATH, 
                                        self.name))
        if code:
            return False
        return True

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

    def __str__(self):
        return "%s" % (self.address)

    def create_dir(self, domain):
        path = "%s/%s/%s" % (settings.STORAGE_PATH, domain.name, self.address)
        if not exec_as_vuser("mkdir -p %s" % path):
            return False
        try:
            mbtype = getattr(settings, "MAILBOX_TYPE")
        except AttributeError:
            mbtype = "maildir"
        if mbtype == "mbox":
            template = ["Inbox", "Drafts", "Sent", "Trash", "Junk"]
            for dir in template:
                exec_as_vuser("touch %s/%s" % (path, dir))
                    
            self.path = "%s/%s/Inbox" % (domain.name, self.address)
        else:
            template = [".Drafts/", ".Sent/", ".Trash/", ".Junk/"]
            for dir in template:
                for sdir in ["cur", "new", "tmp"]:
                    exec_as_vuser("mkdir -p %s/.maildir/%s/%s" % (path, dir, sdir))
            self.path = "%s/%s/.maildir/" % (domain.name, self.address)
        return True

    def rename_dir(self, domain, newaddress):
        path = "%s/%s" % (settings.STORAGE_PATH, domain)
        code, output = exec_pipe("sudo -u %s mv %s/%s %s/%s" \
                                     % (settings.VIRTUAL_UID, 
                                        path, self.address, path, newaddress))
        if code:
            os.system("echo '%s' >> /tmp/vmail.log" % output)
            return False
        self.path = "%s/%s/.maildir/" % (domain, newaddress)
        return True

    def delete_dir(self):
        code, output = exec_pipe("sudo -u %s rm -r %s/%s/%s" \
                                     % (settings.VIRTUAL_UID, 
                                        settings.STORAGE_PATH,
                                        self.domain.name, self.name))
        if code:
            return False
        return True

class Alias(models.Model):
    address = models.CharField(_('address'), max_length=100)
    full_address = models.CharField(max_length=150)
    mbox = models.ForeignKey(Mailbox, verbose_name=_('mailbox'))
    enabled = models.BooleanField(_('enabled'))

    class Meta:
        permissions = (
            ("view_aliases", "View aliases"),
            )
