# coding: utf8
from django.db import models, IntegrityError
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.conf import settings
from modoboa.lib import parameters
from modoboa.lib import exec_cmd, exec_as_vuser, crypt_password
import os
import pwd

class AdminError(Exception):
    """Custom exception

    
    """
    def __init__(self, value):
        """Constructor

        :param value: the information contained in this exception.
        """
        self.value = str(value)
        
    def __str__(self):
        """String representation"""
        return self.value

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
        path = "%s/%s" % (parameters.get_admin("STORAGE_PATH"), self.name)
        return exec_as_vuser("mkdir -p %s" % path)

    def rename_dir(self, newname):
        stpath = parameters.get_admin("STORAGE_PATH")
        return exec_as_vuser("mv %s/%s %s/%s" \
                                 % (stpath, self.name, stpath, newname))

    def delete_dir(self):
        return exec_as_vuser("rm -r %s/%s" \
                                 % (parameters.get_admin("STORAGE_PATH"), 
                                    self.name))

    def delete(self, *args, **kwargs):
        keepdir = False
        if kwargs.has_key("keepdir"):
            keepdir = kwargs["keepdir"]
            del kwargs["keepdir"]
        # Not very optimized but currently, this is the simple way
        # I've found to delete all related objects (mailboxes, users
        # and aliases)!
        for mb in self.mailbox_set.all():
            mb.delete(keepdir=keepdir)
        super(Domain, self).delete(*args, **kwargs)
        if not keepdir:
            self.delete_dir()

    def __str__(self):
        return self.name

class DomainAlias(models.Model):
    name = models.CharField(_("name"), max_length=100, unique=True,
                            help_text=_("The alias name"))
    target = models.ForeignKey(Domain, verbose_name=_('target'),
                               help_text=_("The domain this alias points to"))
    enabled = models.BooleanField(_('enabled'),
                                  help_text=_("Check to activate this alias"))

    class Meta:
        permissions = (
            ("view_domaliases", "View domain aliases"),
            )

class Mailbox(models.Model):
    name = models.CharField(_('name'), max_length=100, 
                            help_text=_("First name and last name of mailbox owner"))
    address = models.CharField(_('address'), max_length=100,
                               help_text=_("Mailbox address (without the @domain.tld part)"))
    password = models.CharField(_('password'), max_length=100)
    quota = models.IntegerField()
    uid = models.IntegerField()
    gid = models.IntegerField()
    path = models.CharField(max_length=255)
    domain = models.ForeignKey(Domain)
    user = models.ForeignKey(User)

    class Meta:
        permissions = (
            ("view_mailboxes", "View mailboxes"),
            )

    def __init__(self, *args, **kwargs):
        super(Mailbox, self).__init__(*args, **kwargs)
        self.mbtype = parameters.get_admin("MAILBOX_TYPE")
        self.mdirroot = parameters.get_admin("MAILDIR_ROOT")
        if not self.mdirroot.endswith('/'):
            self.mdirroot += '/'

    def __str__(self):
        return self.__full_address()

    def __full_address(self):
        return "%s@%s" % (self.address, self.domain.name)

    full_address = property(__full_address)

    def create_dir(self):
        relpath = "%s/%s" % (self.domain.name, self.address)
        abspath = os.path.join(parameters.get_admin("STORAGE_PATH"), relpath)
        if self.mbtype == "mbox":
            self.path = "%s/Inbox" % self.address
        else:
            self.path = "%s/%s" % (self.address, self.mdirroot)
        if os.path.exists(abspath):
            return True
        if not exec_as_vuser("mkdir -p %s" % abspath):
            return False
        if self.mbtype == "mbox":
            template = ["Inbox", "Drafts", "Sent", "Trash", "Junk"]
            for f in template:
                exec_as_vuser("touch %s/%s" % (abspath, f))
        else:
            template = [".Drafts/", ".Sent/", ".Trash/", ".Junk/"]
            for dir in template:
                for sdir in ["cur", "new", "tmp"]:
                    exec_as_vuser("mkdir -p %s/%s/%s/%s" \
                                      % (abspath, self.mdirroot, dir, sdir))
        return True

    def rename_dir(self, domain, newaddress):
        if self.domain.name == domain and newaddress == self.address:
            return True
        path = "%s/%s" % (parameters.get_admin("STORAGE_PATH"), domain)
        code = exec_as_vuser("mv %s/%s %s/%s" \
                                 % (path, self.address, path, newaddress))
        if code:
            self.path = "%s/%s/%s/" % (domain, newaddress, self.mdirroot)
        return code

    def delete_dir(self):
        return exec_as_vuser("rm -r %s/%s/%s" \
                                 % (parameters.get_admin("STORAGE_PATH"),
                                    self.domain.name, self.address))

    def save(self, *args, **kwargs):
        if not self.create_dir():
            raise AdminError(_("Failed to initialise mailbox, check permissions"))
        try:
            user = getattr(self, "user")
        except User.DoesNotExist:
            user = User()
        user.username = user.email = "%s@%s" % (self.address, self.domain.name)
        user.set_unusable_password()
        user.is_active = kwargs["enabled"]
        try:
            fname, lname = self.name.split()
        except ValueError:
            fname = self.name
            lname = ""
        user.first_name = fname
        user.last_name = lname
        try:
            user.save()
        except IntegrityError:
            raise AdminError(_("Mailbox with this address already exists"))
        self.user = user
        if kwargs["password"] != u"é":
            self.password = crypt_password(kwargs["password"])
        self.uid = pwd.getpwnam(parameters.get_admin("VIRTUAL_UID")).pw_uid
        self.gid = pwd.getpwnam(parameters.get_admin("VIRTUAL_GID")).pw_gid
        if kwargs.has_key("quota") and kwargs["quota"] is not None \
                and int(kwargs["quota"]) < self.domain.quota:
            self.quota = kwargs["quota"]
        else:
            self.quota = self.domain.quota
        try:
            for kw in ["enabled", "password", "quota"]:
                del kwargs[kw]
        except KeyError:
            pass
        super(Mailbox, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        keepdir = False
        if kwargs.has_key("keepdir"):
            keepdir = kwargs["keepdir"]
            del kwargs["keepdir"]
        for alias in self.alias_set.all():
            alias.mboxes.remove(self)
            if len(alias.mboxes.all()) == 0:
                alias.delete()
        self.user.delete()
        super(Mailbox, self).delete(*args, **kwargs)
        if not keepdir:
            self.delete_dir()

    def tohash(self):
        return {
            "id" : self.id, 
            "domain" : self.domain.name,
            "full_name" : self.name,
            "enabled" : self.user.is_active
            }

class Alias(models.Model):
    address = models.CharField(_('address'), max_length=254,
                               help_text=_("The alias address (without the domain part)"))
    mboxes = models.ManyToManyField(Mailbox, verbose_name=_('mailboxes'),
                                    help_text=_("The mailboxes this alias points to"))
    enabled = models.BooleanField(_('enabled'),
                                  help_text=_("Check to activate this alias"))

    class Meta:
        permissions = (
            ("view_aliases", "View aliases"),
            )

    def __domain(self):
        return self.mboxes.all()[0].domain

    domain = property(__domain)

class Extension(models.Model):
    name = models.CharField(max_length=150)
    enabled = models.BooleanField(_('enabled'),
                                  help_text=_("Check to enable this extension"))

    def __getmodule(self):
        extname = "modoboa.extensions.%s" % self.name
        return __import__(extname, globals(), locals(), ['main'])

    def load(self):
        self.__getmodule().main.init()

    def unload(self):
        self.__getmodule().main.destroy()

    def on(self):
        self.load()

        extdir = "%s/extensions/%s" % (settings.MODOBOA_DIR, self.name)
        scriptdir = "%s/%s" % (extdir, "scripts")
        if os.path.exists(scriptdir):
            targetdir = os.path.join(settings.MODOBOA_DIR, "scripts")
            exec_cmd("ln -s %s %s/%s" % (scriptdir, targetdir, self.name))

        staticpath = "%s/%s" % (extdir, "static")
        if os.path.exists(staticpath):
            for d in ['css', 'js']:
                subpath = "%s/%s" % (staticpath, d)
                if not os.path.exists(subpath):
                    continue
                exec_cmd("ln -s %s %s/static/%s/%s" % (subpath, settings.MODOBOA_DIR,
                                                       d, self.name))

    def off(self):
        self.unload()

        extdir = "%s/extensions/%s" % (settings.MODOBOA_DIR, self.name)
        scriptdir = "%s/%s" % (extdir, "scripts")
        if os.path.exists(scriptdir):
            target = "%s/scripts/%s" % (settings.MODOBOA_DIR, self.name)
            exec_cmd("rm %s" % target)

        staticpath = "%s/%s" % (extdir, "static")  
        if os.path.exists(staticpath):
            for d in ['css', 'js']:
                subpath = "%s/static/%s/%s" % (settings.MODOBOA_DIR, d, self.name)
                exec_cmd("rm -f %s" % subpath)






